from plots import generate_all_plots_and_findings


def main():
    generate_all_plots_and_findings(formats=("png", "pdf", "svg"))
    print("Exported PNG, PDF, and SVG charts to results/graphs")


if __name__ == "__main__":
    main()
