import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        "Teller", description="A preferential vote counter program."
    )
    parser.add_argument(
        "config_file", type=Path, help="Path to the configuration json file."
    )
    parser.add_argument("vote_file", type=Path, help="Path to the vote csv file.")

    args = parser.parse_args()

    # Sanity Checking
    config_file: Path = args.config_file
    vote_file: Path = args.vote_file
    assert (
        config_file.is_file()
    ), f"No file found at config file location: {config_file}"
    assert vote_file.is_file(), f"No file found at vote file location: {vote_file}"


if __name__ == "__main__":
    main()
