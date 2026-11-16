'''
InflationCalculator.py
Sinem Firat

FINE 3300 Assignment #2 - Part B: Consumer Price Index
InflationCalculator class that reads the Bank of Canada monthly CPI file, graphs
the CPI and its annual percentage change, and replicates the Bank of Canada
Inflation Calculator. The calculator is enhanced so that the user can enter a
month and a year for each period (the website only accepts a year).
'''

import calendar
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class InflationCalculator:
    def __init__(self, file_name="BankOfCanadaCPI.2026.csv"):
        self.__file_name = file_name
        self.__data = None
        self.__read_file()

    def __read_file(self):
        # The file starts with a few lines about the terms and the series.
        # The data starts after the line that says OBSERVATIONS.
        with open(self.__file_name, encoding="utf-8-sig") as file:
            lines = file.readlines()

        start_row = 0
        for i in range(len(lines)):
            if "OBSERVATIONS" in lines[i]:
                start_row = i + 1
                break

        df = pd.read_csv(self.__file_name, skiprows=start_row, encoding="utf-8-sig")
        df.columns = ["Date", "CPI"]
        df["Date"] = pd.to_datetime(df["Date"])

        # Data cleaning: the file has two extra rows (1927-04-30 and 1932-04-30)
        # that repeat the May value. Every monthly value is dated on the 1st,
        # so only those rows are kept.
        df = df[df["Date"].dt.day == 1].copy()

        # Extract the year and the month of each row
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month

        # Annual percentage change: each month compared with the same month one year earlier.
        # With NumPy arrays, the CPI from the 13th month onwards is divided by the CPI
        # 12 months before it. The first 12 months stay empty (NaN) because there is
        # no earlier year to compare them with.
        cpi = df["CPI"].to_numpy()
        annual_change = np.full(len(cpi), np.nan)
        annual_change[12:] = (cpi[12:] / cpi[:-12] - 1) * 100
        df["Annual Change"] = annual_change

        self.__data = df.reset_index(drop=True)

    def get_first_date(self):
        return self.__data["Date"].iloc[0]

    def get_last_date(self):
        return self.__data["Date"].iloc[-1]

    def get_cpi(self, year, month):
        row = self.__data[(self.__data["Year"] == year) & (self.__data["Month"] == month)]
        return row["CPI"].iloc[0]

    def validate_price(self, text):
        # Dollar signs, commas and spaces are allowed (for example $1,250.50)
        text = text.replace("$", "").replace(",", "").replace(" ", "")

        try:
            price = float(text)
        except ValueError:
            return (False, "the price must be a number.")

        # float() also accepts "nan" and "inf", so check that the price is a normal positive number
        if not np.isfinite(price) or price <= 0:
            return (False, "the price must be greater than zero.")

        return (True, price)

    def validate_date(self, text):
        # Accepted formats: YYYY-MM or YYYY/MM (for example 1985-03), or YYYY (year only).
        # With a year only, the latest month in the data is used, the same way the
        # Bank of Canada calculator works.
        parts = text.strip().replace("/", "-").split("-")

        # The year must come first and have 4 digits (so 03/1985 is not read as year 3)
        if len(parts[0]) != 4:
            return (False, "please enter the date as YYYY-MM (for example 1985-03).")

        try:
            year = int(parts[0])
            if len(parts) == 1:
                month = self.get_last_date().month
            elif len(parts) == 2:
                month = int(parts[1])
            else:
                return (False, "please enter the date as YYYY-MM (for example 1985-03).")
        except ValueError:
            return (False, "please enter the date as YYYY-MM (for example 1985-03).")

        if month < 1 or month > 12:
            return (False, "the month must be between 01 and 12.")

        # Make sure the date is inside the data set
        first = self.get_first_date()
        last = self.get_last_date()
        if (year, month) < (first.year, first.month) or (year, month) > (last.year, last.month):
            return (False, "the date must be between {} {} and {} {}.".format(calendar.month_name[first.month], first.year,
                                                                                  calendar.month_name[last.month], last.year))

        return (True, (year, month))

    def calculate(self, price, start, end):
        start_year, start_month = start
        end_year, end_month = end

        cpi_start = self.get_cpi(start_year, start_month)
        cpi_end = self.get_cpi(end_year, end_month)

        # Same formulas as the Bank of Canada calculator
        new_price = price * cpi_end / cpi_start
        percent_change = (new_price - price) / price * 100

        # Number of years, including the months (for example 41.5 years)
        months = (end_year - start_year) * 12 + (end_month - start_month)
        years = months / 12

        # Average annual rate (compounded); it cannot be calculated for the same month
        if months == 0:
            annual_rate = None
        else:
            annual_rate = ((cpi_end / cpi_start) ** (1 / abs(years)) - 1) * 100

        return {"price": price, "new_price": new_price, "start": start, "end": end,
                "cpi_start": cpi_start, "cpi_end": cpi_end, "percent_change": percent_change,
                "months": months, "years": years, "annual_rate": annual_rate}

    def plot_cpi(self, file_name="CPI.png"):
        df = self.__data
        fig, ax = plt.subplots(figsize=(12, 6), layout="constrained")

        # Left axis: CPI and a dotted line through the base level (2002 = 100)
        ax.plot(df["Date"], df["CPI"], color="tab:blue", linewidth=2, label="CPI (2002 = 100)")
        ax.axhline(100, color="black", linestyle=":", linewidth=1.5, label="Base Level (2002 = 100)")
        ax.set_xlabel("Year")
        ax.set_ylabel("CPI [2002 = 100]")
        ax.grid(True, alpha=0.3)

        # Right axis: annual percentage change, with a thin line at 0%
        ax2 = ax.twinx()
        ax2.plot(df["Date"], df["Annual Change"], color="tab:orange", linewidth=1, label="Annual Change [%] (right axis)")
        ax2.axhline(0, color="gray", linewidth=0.8)
        ax2.set_ylabel("Annual Change [%]")

        ax.set_title("Consumer Price Index for Canada, {} to {}".format(df["Year"].iloc[0], df["Year"].iloc[-1]), fontsize=16)

        # One legend for both axes
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc="upper center")

        fig.savefig(file_name, dpi=150)
        plt.show()


def ask_user(prompt, validate):
    # Keep asking until the input is valid
    while True:
        valid, result = validate(input(prompt))
        if valid:
            return result
        print("Invalid input: {}\n".format(result))


def print_results(results):
    start_year, start_month = results["start"]
    end_year, end_month = results["end"]

    if results["annual_rate"] is None:
        annual_rate = "N/A (same month)"
    else:
        annual_rate = "{:.2f}%".format(results["annual_rate"])

    # Labels are padded to 40 characters so that the values line up
    print()
    print("A basket of goods and services that cost ${:,.2f} CAD in {} {}".format(results["price"], calendar.month_name[start_month], start_year))
    print("would cost ${:,.2f} CAD in {} {}.".format(results["new_price"], calendar.month_name[end_month], end_year))
    print()
    print("{:<40}{:,.2f}%".format("Percent change:", results["percent_change"]))
    print("{:<40}{:.2f} ({:,} months)".format("Number of years:", results["years"], results["months"]))
    print("Average annual rate of inflation (%) /")
    print("{:<40}{}".format("Decline in the value of money:", annual_rate))
    print("{:<40}{:.1f}".format("CPI for first period ({} {}):".format(calendar.month_abbr[start_month], start_year), results["cpi_start"]))
    print("{:<40}{:.1f}".format("CPI for second period ({} {}):".format(calendar.month_abbr[end_month], end_year), results["cpi_end"]))
    print()


if __name__ == "__main__":
    calculator = InflationCalculator("BankOfCanadaCPI.2026.csv")

    # Graph of the CPI and its annual percentage change (saved as CPI.png)
    calculator.plot_cpi("CPI.png")

    first = calculator.get_first_date()
    last = calculator.get_last_date()
    print("Bank of Canada Inflation Calculator (monthly CPI data)")
    print("Data available from {} {} to {} {}.".format(calendar.month_name[first.month], first.year,
                                                        calendar.month_name[last.month], last.year))
    print("Enter dates as YYYY-MM (for example 1985-03).\n")

    another = "Y"
    while another == "Y":
        price = ask_user("Enter the price of the goods or services: ", calculator.validate_price)
        start = ask_user("Enter the date of the first period (YYYY-MM): ", calculator.validate_date)
        end = ask_user("Enter the date of the second period (YYYY-MM): ", calculator.validate_date)

        results = calculator.calculate(price, start, end)
        print_results(results)

        another = input("Would you like to do another calculation? (Y/N): ").strip().upper()
