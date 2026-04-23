#-------------------------------------------------------------------------------
# Name:        module4
# Purpose:
#
# Author:      ANANYA SRI TK
#
# Created:     23-04-2026
# Copyright:   (c) ANANYA SRI TK 2026
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import re

app = Flask(__name__)

DATA_FILE = "data.csv"


def load_data():
    df = pd.read_csv(DATA_FILE)
    df.columns = [str(col).strip() for col in df.columns]

    # Try converting columns to numeric where possible
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except Exception:
            pass

    # Derived columns
    if "Marks" in df.columns:
        df["Percentage"] = df["Marks"]

        def get_grade(mark):
            if pd.isna(mark):
                return "N/A"
            if mark >= 90:
                return "A"
            elif mark >= 75:
                return "B"
            elif mark >= 60:
                return "C"
            else:
                return "D"

        df["Grade"] = df["Marks"].apply(get_grade)
        df["Status"] = df["Marks"].apply(
            lambda x: "Pass" if pd.notna(x) and x >= 40 else "Fail"
        )

    # Growth Rate column
    if all(col in df.columns for col in ["Student", "Month", "Marks"]):
        month_order = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
        }

        temp = df.copy()
        temp["MonthOrder"] = temp["Month"].map(month_order)
        temp = temp.dropna(subset=["MonthOrder"])

        if not temp.empty:
            grouped = temp.sort_values("MonthOrder").groupby("Student")["Marks"].agg(["first", "last"])
            grouped = grouped[grouped["first"] != 0]

            growth_map = {}
            for student, row in grouped.iterrows():
                growth = ((row["last"] - row["first"]) / row["first"]) * 100
                growth_map[student] = round(growth, 2)

            df["GrowthRate"] = df["Student"].map(growth_map)

    return df


def get_numeric_columns(df):
    return df.select_dtypes(include=[np.number]).columns.tolist()


def safe_formula_eval(df, formula):
    if not formula or not formula.strip():
        return None, "No formula given"

    allowed_pattern = r"^[A-Za-z0-9_+\-*/().\s]+$"
    if not re.match(allowed_pattern, formula):
        return None, "Invalid characters in formula"

    local_dict = {}
    safe_formula = formula

    for col in df.columns:
        safe_name = col.replace(" ", "_")
        local_dict[safe_name] = df[col]

    for col in sorted(df.columns, key=len, reverse=True):
        safe_formula = re.sub(
            rf"\b{re.escape(col)}\b",
            col.replace(" ", "_"),
            safe_formula
        )

    try:
        result = eval(safe_formula, {"__builtins__": {}}, local_dict)
        return result, None
    except Exception as e:
        return None, f"Invalid formula: {str(e)}"


def generate_insights(df):
    insights = []

    if df.empty:
        return ["No insights available for current selection."]

    # Highest + Lowest scorer
    if "Marks" in df.columns:
        top_row = df.loc[df["Marks"].idxmax()]
        student_name = top_row["Student"] if "Student" in df.columns else "Unknown"
        subject_name = top_row["Subject"] if "Subject" in df.columns else "N/A"
        month_name = top_row["Month"] if "Month" in df.columns else "N/A"
        insights.append(
            f"Highest scorer: {student_name} scored {top_row['Marks']} in {subject_name} ({month_name})."
        )

        low_row = df.loc[df["Marks"].idxmin()]
        low_name = low_row["Student"] if "Student" in df.columns else "Unknown"
        insights.append(f"Lowest scorer: {low_name} scored {low_row['Marks']}.")

    # Subject with most low scores
    if "Subject" in df.columns and "Marks" in df.columns:
        low_scores = df[df["Marks"] < 70]
        if not low_scores.empty:
            weak_subject = low_scores["Subject"].value_counts().idxmax()
            weak_count = low_scores["Subject"].value_counts().max()
            insights.append(
                f"Subject with most low scores: {weak_subject} has {weak_count} scores below 70."
            )

    # Outliers
    if "Marks" in df.columns and "Student" in df.columns:
        avg_marks = df["Marks"].mean()
        high_outliers = sorted(
            df[df["Marks"] > avg_marks + 15]["Student"].dropna().unique().tolist()
        )
        low_outliers = sorted(
            df[df["Marks"] < avg_marks - 15]["Student"].dropna().unique().tolist()
        )

        if high_outliers:
            insights.append(
                "Students well above average: " + ", ".join(high_outliers[:5]) + "."
            )
        if low_outliers:
            insights.append(
                "Students well below average: " + ", ".join(low_outliers[:5]) + "."
            )

    # Attendance mismatch
    if "Attendance" in df.columns and "Marks" in df.columns and "Student" in df.columns:
        mismatch = []

        high_att_low_marks = df[(df["Attendance"] >= 85) & (df["Marks"] < 70)]
        low_att_high_marks = df[(df["Attendance"] < 75) & (df["Marks"] >= 85)]

        for _, row in high_att_low_marks.head(3).iterrows():
            mismatch.append(
                f"{row['Student']} has high attendance ({row['Attendance']}%) but low marks ({row['Marks']})."
            )

        for _, row in low_att_high_marks.head(3).iterrows():
            mismatch.append(
                f"{row['Student']} has low attendance ({row['Attendance']}%) but high marks ({row['Marks']})."
            )

        insights.extend(mismatch)

    # Biggest drop
    if all(col in df.columns for col in ["Student", "Month", "Marks"]):
        month_order = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
        }
        temp = df.copy()
        temp["MonthOrder"] = temp["Month"].map(month_order)

        if temp["MonthOrder"].notna().any():
            grouped = (
                temp.dropna(subset=["MonthOrder"])
                .sort_values("MonthOrder")
                .groupby("Student")["Marks"]
                .agg(["first", "last"])
            )
            grouped["drop"] = grouped["first"] - grouped["last"]
            grouped = grouped.sort_values("drop", ascending=False)
            if not grouped.empty and grouped.iloc[0]["drop"] > 0:
                insights.append(
                    f"Biggest drop in performance: {grouped.index[0]} dropped by {int(grouped.iloc[0]['drop'])} marks over time."
                )

    # Growth rate
    if all(col in df.columns for col in ["Student", "Month", "Marks"]):
        month_order = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
        }

        temp = df.copy()
        temp["MonthOrder"] = temp["Month"].map(month_order)
        temp = temp.dropna(subset=["MonthOrder"])

        if not temp.empty:
            grouped = temp.sort_values("MonthOrder").groupby("Student")["Marks"].agg(["first", "last"])
            grouped = grouped[grouped["first"] != 0]

            if not grouped.empty:
                grouped["growth_rate"] = ((grouped["last"] - grouped["first"]) / grouped["first"]) * 100

                top_growth = grouped.sort_values("growth_rate", ascending=False).head(1)
                top_decline = grouped.sort_values("growth_rate", ascending=True).head(1)

                if not top_growth.empty:
                    insights.append(
                        f"Highest growth rate: {top_growth.index[0]} improved by {round(top_growth.iloc[0]['growth_rate'], 2)}%."
                    )

                if not top_decline.empty:
                    insights.append(
                        f"Largest decline rate: {top_decline.index[0]} changed by {round(top_decline.iloc[0]['growth_rate'], 2)}%."
                    )

    return insights[:10]


def generate_summary_cards(df):
    summary = {}
    summary["Total Records"] = int(len(df))

    if "Student" in df.columns:
        summary["Unique Students"] = int(df["Student"].nunique())

    if "Marks" in df.columns:
        summary["Average Marks"] = round(float(df["Marks"].mean()), 2)
        summary["Highest Marks"] = int(df["Marks"].max())
        summary["Below 70 Count"] = int((df["Marks"] < 70).sum())

    if "Attendance" in df.columns:
        summary["Average Attendance"] = round(float(df["Attendance"].mean()), 2)

    if "GrowthRate" in df.columns:
        growth_series = df["GrowthRate"].dropna()
        if not growth_series.empty:
            summary["Average Growth %"] = round(float(growth_series.mean()), 2)

    return summary


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get-columns", methods=["GET"])
def get_columns():
    try:
        df = load_data()
        return jsonify({
            "columns": df.columns.tolist(),
            "numeric_columns": get_numeric_columns(df)
        })
    except Exception as e:
        return jsonify({
            "columns": [],
            "numeric_columns": [],
            "error": str(e)
        }), 500


@app.route("/check-data")
def check_data():
    df = load_data()
    return {
        "rows": int(len(df)),
        "columns": df.columns.tolist(),
        "first_5_rows": df.head(5).to_dict(orient="records")
    }


@app.route("/generate-report", methods=["POST"])
def generate_report():
    try:
        df = load_data()
        req = request.json or {}

        selected_columns = req.get("columns", [])
        filter_column = req.get("filter_column", "")
        filter_value = req.get("filter_value", "")
        sort_column = req.get("sort_column", "")
        sort_order = req.get("sort_order", "asc")
        calculation = req.get("calculation", "")
        calc_column = req.get("calc_column", "")
        custom_formula = req.get("custom_formula", "").strip()
        row_limit = req.get("row_limit", 50)

        # Filter
        if filter_column and str(filter_value).strip():
            if filter_column in df.columns:
                if pd.api.types.is_numeric_dtype(df[filter_column]):
                    try:
                        value = float(filter_value)
                        df = df[df[filter_column] > value]
                    except Exception:
                        pass
                else:
                    df = df[
                        df[filter_column].astype(str).str.lower()
                        == str(filter_value).lower()
                    ]

        # Custom formula
        if custom_formula:
            formula_result, formula_error = safe_formula_eval(df, custom_formula)
            if formula_error is None:
                if hasattr(formula_result, "round"):
                    df["CustomFormula"] = formula_result.round(2)
                else:
                    df["CustomFormula"] = formula_result
            else:
                return jsonify({"error": formula_error}), 400

        # Sort
        if sort_column and sort_column in df.columns:
            ascending = sort_order == "asc"
            df = df.sort_values(by=sort_column, ascending=ascending, na_position="last")

        # Summary + insights
        summary_cards = generate_summary_cards(df)
        insights = generate_insights(df)

        # Calculation
        result = None
        if calculation and calc_column and calc_column in df.columns:
            if pd.api.types.is_numeric_dtype(df[calc_column]):
                series = df[calc_column].dropna()
                if not series.empty:
                    if calculation == "average":
                        result = round(float(series.mean()), 2)
                    elif calculation == "sum":
                        result = round(float(series.sum()), 2)
                    elif calculation == "max":
                        result = round(float(series.max()), 2)
                    elif calculation == "min":
                        result = round(float(series.min()), 2)

        # Select only chosen columns
        if selected_columns:
            valid_columns = [col for col in selected_columns if col in df.columns]
            if "CustomFormula" in df.columns and "CustomFormula" not in valid_columns:
                valid_columns.append("CustomFormula")
            if valid_columns:
                df = df[valid_columns]

        try:
            row_limit = int(row_limit)
        except Exception:
            row_limit = 50

        if row_limit > 0:
            df = df.head(row_limit)

        df = df.replace({np.nan: None})

        return jsonify({
            "rows": df.to_dict(orient="records"),
            "calculation_result": result,
            "insights": insights,
            "summary_cards": summary_cards
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)