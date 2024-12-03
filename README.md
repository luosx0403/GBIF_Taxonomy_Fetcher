# GBIF-Taxonomy-Fetcher

GBIF (Global Biodiversity Information Facility) is an international network and data platform providing open access to biodiversity data, and its API enables retrieval of species occurrence, taxonomy, and metadata.

This is a powerful Python tool for fetching plant taxonomy information using the [GBIF API](https://www.gbif.org/developer/species).  
Easily retrieve taxonomic classifications from kingdom to species for given plant names with batch processing and parallel support.

---

## 🌟 Features

- **Flexible Input/Output Levels**: Specify the taxonomic levels you need (e.g., family to genus or species to kingdom).
- **Batch Processing**: Process hundreds of plant names from a text file in one go.
- **Parallel Execution**: Accelerate processing with multithreaded requests.
- **Retry Mechanism**: Handles API rate limits and network issues automatically.
- **Customizable Output**: Supports `txt`, `csv`, and `json` formats for easy data integration.
- **Detailed Logging**: Tracks errors and warnings for better troubleshooting.

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.7+**  
   Install Python from [python.org](https://www.python.org/) or use your own package manager.
   
2. **Dependencies**  
   Install required Python libraries:
   ```bash
   pip install requests tqdm
   ```

### Installation

Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/luosx0403/GBIF_Taxonomy_Fetcher.git
cd GBIF_Taxonomy_Fetcher
```

---

## 🔧 Usage

Run the script with the following command:
```bash
python script.py -in-level f -out-level g s -input-file input.txt -output-file output.txt
```
### Taxonomic Levels

This script uses the following abbreviations for taxonomic levels:

| Abbreviation | Full Term | Example         |
| ------------ | --------- | ----------------|
| `k`          | Kingdom   | Plantae         |
| `p`          | Phylum    | Tracheophyta    |
| `c`          | Class     | Magnoliopsida   |
| `o`          | Order     | Rosales         |
| `f`          | Family    | Rosaceae        |
| `g`          | Genus     | Rosa            |
| `s`          | Species   | *Rosa gallica*  |

For example, if you want to fetch the genus (`g`) and species (`s`) for a list of plant family names (`f`), you can specify:

```bash
-in-level f -out-level g s
```

This will return genus and species for each family in the input file.

### Command-Line Arguments

| Argument         | Description                                                                                                   | Example                                |
|------------------|---------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `-in-level`      | Input taxonomic level (`k`, `p`, `c`, `o`, `f`, `g`, `s`)                                                    | `-in-level f`                          |
| `-out-level`     | Output taxonomic levels (multiple values supported, separated by space)                                       | `-out-level g s`                       |
| `-input-file`    | Input file containing plant names (one name per line)                                                        | `-input-file input.txt`                |
| `-output-file`   | Output file for results                                                                                      | `-output-file output.csv`              |
| `-delay`         | Delay between requests (to handle rate limits)                                                               | `-delay 1.5`                           |
| `-parallel`      | Enable multithreaded processing                                                                              | `-parallel`                            |
| `-output-format` | Output file format: `txt`, `csv`, or `json`                                                                  | `-output-format csv`                   |
| `-log-level`     | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`                                            | `-log-level INFO`                      |
| `-retry`         | Retry fetching failed queries (from the error log)                                                           | `-retry`                               |

---

## 📝 Examples

### Example 1: Basic Usage
Retrieve genus and species information for plants listed in `input.txt`, output results to `output.txt`:
```bash
python script.py -in-level f -out-level g s -input-file input.txt -output-file output.txt
```

### Example 2: CSV Output
Output results in CSV format:
```bash
python script.py -in-level g -out-level k p -input-file input.txt -output-file results.csv -output-format csv
```

### Example 3: Parallel Processing
Enable multithreading for faster results:
```bash
python script.py -in-level g -out-level s -input-file plants.txt -output-file output.json -parallel
```

---

## 📁 Input File Format

The input file should be a plain text file with one plant name per line. Example:
```
Rosaceae
Lamiaceae
Poaceae
```

---

## 📊 Output Examples

### TXT Output
```plaintext
Family      Genus      Species
Rosaceae    Rosa       Rosa gallica
Lamiaceae   Mentha     Mentha spicata
Poaceae     Zea        Zea mays
```

### CSV Output
```csv
Family,Genus,Species
Rosaceae,Rosa,Rosa gallica
Lamiaceae,Mentha,Mentha spicata
Poaceae,Zea,Zea mays
```

### JSON Output
```json
[
    {"Family": "Rosaceae", "Genus": "Rosa", "Species": "Rosa gallica"},
    {"Family": "Lamiaceae", "Genus": "Mentha", "Species": "Mentha spicata"},
    {"Family": "Poaceae", "Genus": "Zea", "Species": "Zea mays"}
]
```

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve this tool or report issues, feel free to create a pull request or issue in the repository.

---

## 🧑‍💻 Author

For inquiries, please contact [luoshaoxuan@outlook.com](mailto:luoshaoxuan@outlook.com).
