import numpy as np
import pandas as pd
import json
import os
import sys
import argparse
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Just some colors to make the terminal look less depressing
class Color:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @staticmethod
    def print(text, color=END):
        print(f"{color}{text}{Color.END}")

# --- Data Structures ---

@dataclass
class Semester:
    id: int
    credits: float
    sgpa: Optional[float] = None # None means it hasn't happened yet (the mystery box)

@dataclass
class StudentProfile:
    # storing semesters in a map because O(1) > O(n) or something
    semesters: Dict[int, Semester] = field(default_factory=dict)
    extraCredits: float = 0.0
    extraGrade: float = 10.0
    targets: List[float] = field(default_factory=lambda: [8.5, 9.0])

    def toDict(self):
        return {
            "semesters": {
                k: {"credits": v.credits, "sgpa": v.sgpa} 
                for k, v in self.semesters.items()
            },
            "extraCredits": self.extraCredits,
            "extraGrade": self.extraGrade,
            "targets": self.targets
        }

    @staticmethod
    def fromDict(data):
        profile = StudentProfile()
        for k, v in data["semesters"].items():
            profile.semesters[int(k)] = Semester(int(k), v["credits"], v["sgpa"])
        profile.extraCredits = data.get("extraCredits", 0.0)
        profile.extraGrade = data.get("extraGrade", 10.0)
        profile.targets = data.get("targets", [8.5, 9.0])
        return profile

    @property
    def completedSems(self):
        # returns the semesters where you actually laid down your cards
        return [s for s in self.semesters.values() if s.sgpa is not None]

    @property
    def futureSems(self):
        # returns the semesters that are still haunting your dreams
        return [s for s in self.semesters.values() if s.sgpa is None]

# --- Interactive Setup ---
def interactiveSetup() -> StudentProfile:
    Color.print("\n=== CGPA Predictor Setup ===", Color.CYAN)
    profile = StudentProfile()
    
    # figuring out the past damage
    while True:
        try:
            nDone = int(input("How many semesters have you survived so far? "))
            break
        except ValueError:
            pass
            
    for i in range(1, nDone + 1):
        print(f"\n--- Semester {i} ---")
        cr = float(input(f"Credits for Sem {i}: "))
        sg = float(input(f"SGPA for Sem {i}: "))
        profile.semesters[i] = Semester(i, cr, sg)

    # figuring out the future struggle
    while True:
        try:
            nFuture = int(input("\nHow many semesters related to torture are left? "))
            break
        except ValueError:
            pass
            
    startSem = nDone + 1
    for i in range(startSem, startSem + nFuture):
        print(f"\n--- Semester {i} (Future) ---")
        cr = float(input(f"Credits for Sem {i}: "))
        profile.semesters[i] = Semester(i, cr, None)

    # checking for free lunches (extra credits)
    ans = input("\nDo you have extra credits (clubs, yoga, touching grass)? (y/n): ").lower()
    if ans == 'y':
        profile.extraCredits = float(input("Total Extra Credits: "))
        profile.extraGrade = float(input("Grade point for these (usually 10, don't lie): "))

    # setting the impossible goals
    tInput = input("\nEnter target CGPAs (comma separated, e.g., '8.5, 9.0'): ")
    profile.targets = [float(x.strip()) for x in tInput.split(",")]

    return profile

# --- Simulation Logic ---
class Simulator:
    def __init__(self, profile: StudentProfile):
        self.profile = profile
        
        # let's crunch the numbers from the past
        self.pastCreditsArr = np.array([s.credits for s in profile.completedSems])
        self.pastScoresArr = np.array([s.sgpa for s in profile.completedSems])
        self.pastPoints = np.sum(self.pastCreditsArr * self.pastScoresArr)
        self.pastTotalCredits = np.sum(self.pastCreditsArr)
        
        # prepping for the future
        self.futureCreditsArr = np.array([s.credits for s in profile.futureSems])
        self.futureTotalCredits = np.sum(self.futureCreditsArr)
        self.nFuture = len(profile.futureSems)

    def calculateRequiredAverage(self, target, useExtra=False):
        # calculate exactly how much sleep you need to lose to hit the target
        finalCredits = self.pastTotalCredits + self.futureTotalCredits
        finalPointsOffset = 0
        
        if useExtra:
            finalCredits += self.profile.extraCredits
            finalPointsOffset = self.profile.extraCredits * self.profile.extraGrade

        # math time: solving for X where X is the average required
        neededFuturePts = (target * finalCredits) - self.pastPoints - finalPointsOffset
        
        if self.futureTotalCredits == 0: return 0.0
        return neededFuturePts / self.futureTotalCredits

    def runMonteCarlo(self, nSims=5000):
        # predicting the future by rolling dice 5000 times
        
        scenarios = {
            "Chill Mode (~8.0)": np.full(self.nFuture, 8.0),
            "Consistent (~8.5)": np.full(self.nFuture, 8.5),
            "Push Hard (~9.2)": np.full(self.nFuture, 9.2),
            "Topper Mode (~9.6)": np.full(self.nFuture, 9.6)
        }
        
        # if have more than 1 semester left, let's try a crazy strategy
        if self.nFuture >= 2:
            mixed = np.full(self.nFuture, 8.5)
            mixed[0] = 9.2 # putting all eggs in the next basket
            scenarios["Push Next Sem Only"] = mixed

        results = []

        Color.print("\nRunning Monte Carlo Simulations (consulting the crystal ball)...", Color.YELLOW)
        
        for name, means in scenarios.items():
            # generating random outcomes because life is random
            meansCol = means.reshape(self.nFuture, 1)
            noise = np.random.normal(0, 0.3, (self.nFuture, nSims))
            simSgpas = np.clip(meansCol + noise, 5.0, 10.0)
            
            # calculating the weighted average
            futurePts = np.sum(simSgpas * self.futureCreditsArr.reshape(self.nFuture, 1), axis=0)
            
            # base CGPA without the extra seasoning
            totalPts = self.pastPoints + futurePts
            totalCr = self.pastTotalCredits + self.futureTotalCredits
            cgpaBase = totalPts / totalCr
            
            # CGPA with the extra bits
            totalPtsEx = totalPts + (self.profile.extraCredits * self.profile.extraGrade)
            totalCrEx = totalCr + self.profile.extraCredits
            cgpaEx = totalPtsEx / totalCrEx
            
            row = {
                "Scenario": name,
                "Avg CGPA": np.mean(cgpaBase),
                "Max Potential": np.max(cgpaBase)
            }
            
            # calculating probabilities of success vs despair
            for t in self.profile.targets:
                prob = np.mean(cgpaBase >= t) * 100
                probEx = np.mean(cgpaEx >= t) * 100
                row[f"P(>{t})"] = prob
                row[f"P(>{t}) +Extra"] = probEx
                
            results.append(row)
            
        return pd.DataFrame(results)

# --- Main CLI ---
def main():
    parser = argparse.ArgumentParser(description="CGPA Predictor & Simulator")
    parser.add_argument("--reset", action="store_true", help="Reset configuration")
    args = parser.parse_args()

    configFile = "cgpa_config.json"
    
    # load it or lose it
    if not os.path.exists(configFile) or args.reset:
        profile = interactiveSetup()
        with open(configFile, "w") as f:
            json.dump(profile.toDict(), f, indent=4)
        Color.print(f"\nConfiguration saved to {configFile}", Color.GREEN)
    else:
        with open(configFile, "r") as f:
            profile = StudentProfile.fromDict(json.load(f))
        Color.print(f"Loaded configuration from {configFile}", Color.CYAN)

    sim = Simulator(profile)
    
    # 1. Status Report
    Color.print("\n=== Current Status ===", Color.BOLD)
    currCgpa = sim.pastPoints / sim.pastTotalCredits
    print(f"Credits Done: {sim.pastTotalCredits}")
    print(f"Current CGPA: {currCgpa:.4f}")
    
    # 2. Requirements Analysis
    Color.print("\n=== Required Average SGPA for Future Semesters ===", Color.BOLD)
    print(f"{'Target':<10} | {'Base Reqd':<12} | {'With Extra Credits':<18}")
    print("-" * 45)
    for t in profile.targets:
        req = sim.calculateRequiredAverage(t, False)
        reqEx = sim.calculateRequiredAverage(t, True)
        
        rStr = f"{req:.4f}" if req <= 10 else f"{Color.RED}> 10.0{Color.END}"
        exStr = f"{reqEx:.4f}" if reqEx <= 10 else f"{Color.RED}> 10.0{Color.END}"
        
        if req <= 10: rStr = f"{Color.GREEN}{rStr}{Color.END}"
        if reqEx <= 10: exStr = f"{Color.GREEN}{exStr}{Color.END}"
        
        print(f"{t:<10} | {rStr:<21} | {exStr:<29}")

    # 3. Simulation
    df = sim.runMonteCarlo()
    
    Color.print("\n=== Simulation Results ===", Color.BOLD)
    # cleaning up the table for viewing pleasure
    cols = ["Scenario", "Avg CGPA"] + [c for c in df.columns if "P(>" in c]
    print(df[cols].to_string(index=False, float_format="%.2f"))
    
    Color.print("\nVerdicts:", Color.CYAN)
    for t in profile.targets:
        maxProb = df[f"P(>{t}) +Extra"].max()
        if maxProb < 1:
            print(f"- Target {t}: {Color.RED}Impossible/Highly Unlikely{Color.END} (Max Prob: {maxProb:.1f}%)")
        elif maxProb < 50:
            print(f"- Target {t}: {Color.YELLOW}Difficult{Color.END} (Need to sweat significantly)")
        else:
            print(f"- Target {t}: {Color.GREEN}Achievable{Color.END} (You got this)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
