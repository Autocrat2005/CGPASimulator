# CGPA Predictor & Simulator 🔮

**Scientifically calculating if you are "cooked" or not.**

Ever wondered if one bad semester ruined your chances at a 9.0? Same. That's why I built this.

**CGPA Predictor** is a CLI tool that uses **Monte Carlo simulations** (fancy math for "rolling the dice 5,000 times") to predict your academic fate. Instead of generating anxiety, it generates data.

## ⚡ What it actually does

*   **Reality Checks**: Tells you *exactly* what average you need for the next few semesters to hit an 8.5 or 9.0. (No more napkin math).
*   **Parallel Universes**: Simulates 5,000 future scenarios—from "Academic Weapon" to "Just Vibing"—to calculate the statistical probability of you hitting your target.
*   **Touch Grass Credits**: Native support for extra credits (clubs, sports, yoga) to see if they can save your degree.
*   **Saves Your Data**: Remembers your grades in a config file so you don't have to type them every time you panic check.

## 📦 How to Run

1.  **Clone the repo**:
    ```bash
    git clone https://github.com/yourusername/cgpa-predictor.git
    cd cgpa-predictor
    ```

2.  **Install dependencies** (just numpy & pandas):
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run it**:
    ```bash
    python cgpa_predictor.py
    ```

## 🧮 The Logic (For Nerds)

The tool uses two main approaches:
1.  **Algebra**: Reverse-engineers the required SGPA for your target.
    X = (Target * Total Credits - Past Points) / Future Credits
2.  **Monte Carlo**: Generates random SGPAs based on normal distributions ($\mu=SGPA, \sigma=0.3$) for remaining semesters and aggregates the results.

---
*Built with NumPy because doing math by hand is for 1st years.*

