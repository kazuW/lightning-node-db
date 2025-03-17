# Lightning Node Database

This project is designed to manage time-series data for Lightning Network node channels using SQLite3. It provides functionality to retrieve channel lists and channel data, update the database, and optionally delete old data based on a specified retention period.

## Project Structure

python 3.11.3
poetry 1.5.1

```
lightning-node-db
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── db
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── models.py(no use)
│   ├── api
│   │   ├── __init__.py
│   │   ├── lightning_client.py
│   │   └── node_service.py(no use)
│   ├── utils
│   │   ├── __init__.py
│   │   └── config.py
│   └── cli
│       ├── __init__.py
│       └── gitdb.py
├── data
│   └── .gitkeep
├── tests
│   ├── __init__.py
│   ├── test_database.py
│   └── test_node_service.py
├── config.yaml
├── requirements.txt
├── setup.py
└── README.md
```

## Features

1. **Channel List Management**: Retrieve and update the list of channels from the Lightning Network node.
2. **Channel Data Storage**: Store time-series data for each channel, including balances and fees.
3. **Data Retention**: Optionally delete old data based on a specified retention period.
4. **SQLite3 Database**: Utilize SQLite3 for lightweight and efficient data storage.

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd lightning-node-db
   ```

2. Install the required packages:
   ```
   poetry install
   ```

3. Configure the application by editing `config.yaml` to set database connection details and retention periods.

## Usage

To run the application, execute the following command:
```
poetry run python src/main.py
```

You can also use command-line options to manage old data:
```
python src/main.py --delete <number_of_months>
```
"By running it periodically, you will accumulate data."　　
　　
## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
