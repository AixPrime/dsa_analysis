import json
import csv
import re
from datetime import datetime
import os
import argparse

today = datetime.today().strftime('%y%m%d')

class DsaStats:
    def __init__(self):
        super(DsaStats, self).__init__()
        self.traits = ["MU", "KL", "IN", "CH", "FF", "GE", "KO", "KK"]
        self.traitsLong = ["Mut", "Klugheit", "Intuition", "Charisma", "Fingerfertigkeit", "Gewandtheit", "Konstitution", "Körperkraft"]
        with open('../dsa_rolls_analysis/data/json/users.json', 'r') as file:
            users_data = json.load(file)
        self.characters = users_data["users"]
        self.currentChar = ""
        self.charactersWithColon = [char + ":" for char in self.characters]
        self.talentsFile = json.load(open('../dsa_rolls_analysis/data/json/talents.json'))
        self.user_corrections = json.load(open('../dsa_rolls_analysis/data/json/user_corrections.json'))
        self.talent_corrections = json.load(open('../dsa_rolls_analysis/data/json/talent_corrections.json'))
        self.traitsRolls = []
        self.talentsRolls = []
        self.spellsRolls = []
        self.attacksRolls = []
        self.initiativesRolls = []
        self.totalDmg = {char: 0 for char in self.characters}
        self.traitUsageCounts = {char: {trait: 0 for trait in self.traits} for char in self.characters if char not in self.user_corrections}
        self.traitValues = {char: {trait: 0 for trait in self.traits} for char in self.characters if char not in self.user_corrections}

        self.directoryDateDependent = f'../dsa_rolls_analysis/data/rolls_results/{today}_rolls_results/'
        self.directoryRecent = f'../dsa_rolls_analysis/data/rolls_results/000000_rolls_results_recent/'

    # retrieved chatlog parsing
    def process_chatlog(self, chatlog_path):
        with open(chatlog_path, 'r') as chatlogFile:
            chatlogLines = chatlogFile.readlines()
        return chatlogLines

    # Esnure the directory for result files exist or is created
    def ensure_directories(self):
        # Create directories if they don't exist
        if not os.path.exists(self.directoryDateDependent):
            os.makedirs(self.directoryDateDependent)
        if not os.path.exists(self.directoryRecent):
            os.makedirs(self.directoryRecent)

    # Data cleanup functions
    def currentCharCorrection(self, username):
        return self.user_corrections.get(username, username)

    def talentsCurrection(self, talent):
        return self.talent_corrections.get(talent, talent)

    # Potential event cleanup functions
    def validate_item(self, item, category):
        for entry in self.talents_file[category]:
            if entry[category[:-1]] == item:
                return True
        return False

    def validateTrait(self, potentialTrait: str):
        if potentialTrait in self.traitsLong:
            return True
        return False

    def validateTalent(self, potentialTalent: str):
        for i in self.talentsFile["talents"]:
            if i["talent"] == potentialTalent:
                return True
        return False

    def validateSpell(self, potentialSpell: str):
        for i in self.talentsFile["spells"]:
            if i["spell"] == potentialSpell:
                return True
        return False

    def validateAttack(self, potentialAttack: str):
        for i in self.talentsFile["attacks"]:
            if i["attack"] == potentialAttack:
                return True
        return False

    # In den talents nach gewürfeltem Talent suchen
    def getTraits(self,talentOrSpell: str, talent: str):
        for k in self.talentsFile[talentOrSpell+"s"]:
            if k[talentOrSpell] == talent:
                return k["category"], k["trait1"], k["trait2"], k["trait3"]

    def updateTraitUsage(self, character, traits):
        # If it was a specific trait roll, then it's not an array but only a string representing on trait to add
        if traits in self.traits:
            self.traitUsageCounts[character][traits] += 1
        # for talents, and spell rolls an array with the 3 traits needs to be added
        else:
            for trait in traits:
                if trait in self.traits:
                    self.traitUsageCounts[character][trait] += 1

    def updateTraitValues(self, character, traits, traitValues):
        for trait in traits:
            self.traitValues[character][trait] = traitValues[traits.index(trait)]

    def modAndSuccessCheck(self, secondLine: str):
        # Wurfmodifikator
        currentMod = re.split(r' ', secondLine)[1]
        if "±" in currentMod:
            currentMod = currentMod.replace("±", "")
        currentMod = int(currentMod)

        # Wurferfolg
        currentSuccess = 0
        if "gelungen" in secondLine:
            currentSuccess = 1

        return currentSuccess, currentMod

    def talentResult(self, secondLine: str, thirdLine: str):
        # Wurfmodifikator und Wurferfolg checken
        currentSuccess, currentMod = self.modAndSuccessCheck(secondLine)

        # Wurf TaP (Talentpunkte)/ ZfP (Zauberpunkte) /EP (Eigenschaftsprobe)
        if "automatisch" in secondLine:
            currentTaPZfP = int(re.split(r' TaP\*\)\.', re.split(r'\(', secondLine)[2])[0])
        elif "automatisch" not in secondLine:
            currentTaPZfP = int(re.split(r' TaP\*\)\.', re.split(r'\(', secondLine)[1])[0])
        
        # Wurfeigenschaften bspw.: KL/IN/IN = 14/15/15
        currentTraitLevel = re.split(r'/',(re.split(r'Eigenschaften: ', thirdLine))[1])

        #Wurf TaW (Talentwert) / ZfW (Zauberpunkte)     
        currentTaWZfW = int(re.split(r'TaW: ', (re.split(r'Eigenschaften: ', thirdLine))[0])[1].replace(" ", ""))

        return currentMod, currentSuccess, currentTaPZfP, currentTaWZfW, int(currentTraitLevel[0]), int(currentTraitLevel[1]), int(currentTraitLevel[2])

    def spellResult(self, secondLine: str, thirdLine: str):
        # Wurfmodifikator und Wurferfolg checken
        currentSuccess, currentMod = self.modAndSuccessCheck(secondLine)

        # Wurf TaP (Talentpunkte)/ ZfP (Zauberpunkte) /EP (Eigenschaftsprobe)   
        if "automatisch" in secondLine:
            currentTaPZfP = int(re.split(r' ZfP\*\)\.', re.split(r'\(', secondLine)[2])[0])
        elif "automatisch" not in secondLine:
            currentTaPZfP = int(re.split(r' ZfP\*\)\.', re.split(r'\(', secondLine)[1])[0])

        # Wurfeigenschaften bspw.: KL/IN/IN = 14/15/15
        currentTraitLevel = re.split(r'/',(re.split(r'Eigenschaften: ', thirdLine))[1])

        #Wurf TaW (Talentwert) / ZfW (Zauberpunkte)
        currentTaWZfW = int(re.split(r'ZfW: ', (re.split(r'Eigenschaften: ', thirdLine))[0])[1].replace(" ", ""))

        return currentMod, currentSuccess, currentTaPZfP, currentTaWZfW, int(currentTraitLevel[0]), int(currentTraitLevel[1]), int(currentTraitLevel[2])

    def traitResult(self, secondLine: str,thirdLine: str):
        # Wurfmodifikator und Wurferfolg checken
        currentSuccess, currentMod = self.modAndSuccessCheck(secondLine)

        # Wurf TaP (Talentpunkte)/ ZfP (Zauberpunkte) /EP (Eigenschaftsprobe)
        if "automatisch" in secondLine:
            currentTaPZfP = int(re.split(r' EP\*\)\.', re.split(r'\(', secondLine)[2])[0])
        elif "automatisch" not in secondLine:
            currentTaPZfP = int(re.split(r' EP\*\)\.', re.split(r'\(', secondLine)[1])[0])
        
        #Wurf TaW (Talentwert) / ZfW (Zauberpunkte)
        currentTaWZfW = int(re.split(r'EW: ', (re.split(r'Eigenschaften: ', thirdLine))[0])[1].replace(" ", ""))

        return currentMod, currentSuccess, currentTaPZfP, currentTaWZfW
        
    def attackResult(self, secondLine: str,thirdLine: str):
        # Wurfmodifikator
        currentMod = re.split(r' ', secondLine)[1]
        if "±" in currentMod:
            currentMod = currentMod.replace("±", "")
        currentMod = int(currentMod)


        #Wurf TaW (Talentwert) / ZfW (Zauberpunkte)
        # Improved parsing for currentTaWZfW
        try:
            # Extract the numeric value after 'AT-Wert:', 'PA-Wert:', etc.
            currentTaWZfW = int(re.search(r'(\d+)', thirdLine).group())
        except (ValueError, AttributeError):
            print(f"Error parsing TaW/ZfW in line: {thirdLine}")
            currentTaWZfW = 0

        # Wurf TaP (Talentpunkte)/ ZfP (Zauberpunkte) /EP (Eigenschaftsprobe)
        currentTaPZfP = currentTaWZfW - int(re.split(r'\)\.', re.split(r'\(', secondLine)[1])[0]) - currentMod

        currentSuccess = 1
        if currentTaPZfP < 0:
            currentSuccess = 0

        return currentMod, currentSuccess, currentTaPZfP, currentTaWZfW

    def initativeResult(self, firstLine: str, secondLine: str):
        rolledIni = int(re.split(r' ', firstLine)[4])
        currentIni = int(re.split(r' ', secondLine)[2].replace("\tBE:","").replace("\tBE:\tMod.:","").replace("\tMod.:",""))
        currentMod = int(re.split(r' ', secondLine)[-1])
        return currentIni, rolledIni, currentMod

    def writeTraitUsageCounts(self):
        with open(self.directoryDateDependent + f'{today}_trait_usage.csv', 'w', newline='', encoding='utf8') as file:
            writer = csv.writer(file)
            writer.writerow(["Character"] + self.traits)
            for char, counts in self.traitUsageCounts.items():
                writer.writerow([char] + [counts[trait] for trait in self.traits])

        with open(self.directoryRecent + 'trait_usage.csv', 'w', newline='', encoding='utf8') as file:
            writer = csv.writer(file)
            writer.writerow(["Character"] + self.traits)
            for char, counts in self.traitUsageCounts.items():
                try:
                    writer.writerow([char] + [counts[int(trait)] for trait in self.traits])
                except ValueError:
                    writer.writerow([char] + [counts[trait] for trait in self.traits])

    def writeTraitValues(self):
        with open(self.directoryDateDependent + f'{today}_trait_values.csv', 'w', newline='', encoding='utf8') as file:
            writer = csv.writer(file)
            writer.writerow(["Character"] + self.traits)
            for char, value in self.traitValues.items():
                writer.writerow([char] + [value[trait] for trait in self.traits])

        with open(self.directoryRecent + 'trait_values.csv', 'w', newline='', encoding='utf8') as file:
            writer = csv.writer(file)
            writer.writerow(["Character"] + self.traits)
            for char, value in self.traitValues.items():
                try:
                    writer.writerow([char] + [value[int(trait)] for trait in self.traits])
                except ValueError:
                    writer.writerow([char] + [value[trait] for trait in self.traits])

    def writeRollsToFile(self, rolls, rollType, filename):
        
        with open(self.directoryDateDependent + filename, 'w', newline='', encoding='utf8') as file:
            writer = csv.writer(file)
            
            if rollType == 'traits':
                writer.writerow(["Character", "Kategorie", "Talent", "Eigenschaft 1", "Modifikator", "Erfolg", "TaP/ZfP", "TaW/ZfW"])
                writer.writerows(rolls)
            elif rollType == 'talents' or rollType == 'spells':
                writer.writerow(["Character", "Kategorie", "Talent", "Eigenschaft 1", "Eigenschaft 2", "Eigenschaft 3", "Modifikator", "Erfolg", "TaP/ZfP", "TaW/ZfW", "Eigenschaftswert 1", "Eigenschaftswert 2", "Eigenschaftswert 3"])
                writer.writerows(rolls)

            elif rollType == 'attacks':
                writer.writerow(["Character", "Kategorie", "Talent", "Modifikator", "Erfolg", "TaP/ZfP", "TaW/ZfW"])
                writer.writerows(rolls)

            elif rollType == 'initiative':
                writer.writerow(["Character", "Kategorie", "Talent", "Modifikator", "TaP/ZfP", "TaW/ZfW"])
                writer.writerows(rolls)
            else:
                print(f'no database for {rolls}')

        with open(self.directoryRecent + f'{rollType}.csv', 'w', newline='', encoding='utf8') as file:
            writer = csv.writer(file)
            
            if rollType == 'traits':
                writer.writerow(["Character", "Kategorie", "Talent", "Eigenschaft 1", "Modifikator", "Erfolg", "TaP/ZfP", "TaW/ZfW"])
                writer.writerows(rolls)
            elif rollType == 'talents' or rollType == 'spells':
                writer.writerow(["Character", "Kategorie", "Talent", "Eigenschaft 1", "Eigenschaft 2", "Eigenschaft 3", "Modifikator", "Erfolg", "TaP/ZfP", "TaW/ZfW", "Eigenschaftswert 1", "Eigenschaftswert 2", "Eigenschaftswert 3"])
                writer.writerows(rolls)

            elif rollType == 'attacks':
                writer.writerow(["Character", "Kategorie", "Talent", "Modifikator", "Erfolg", "TaP/ZfP", "TaW/ZfW"])
                writer.writerows(rolls)

            elif rollType == 'initiative':
                writer.writerow(["Character", "Kategorie", "Talent", "Modifikator", "TaP/ZfP", "TaW/ZfW"])
                writer.writerows(rolls)
            else:
                print(f'no database for {rolls}')

            
    def countDmg(self, secondLine: str):
        currentDmg = int(re.split(r' ', secondLine)[0])
        self.totalDmg[self.currentChar] += currentDmg


    # Erstellt eine Excel/CSV Datei mit allen gewürfelten Talenten aller angegebnen Charaktere
    def main(self, chatlogLines):

        self.ensure_directories()
        #Dafür wird die chatLogFile geöffnet und die Lines ausgelesen und anschließen jede Line nach einem Charakter durchsucht um das folgende Talent festzustellen
        #chatlogFile = open('../data/chatlogs/231110_chatlog.txt', 'r')
        #chatlogLines = chatlogFile.readlines()
        nonUsedLines = []

        for i in range(len(chatlogLines)):
            potentialEvent = chatlogLines[i].strip()
            if potentialEvent in self.charactersWithColon:
                self.currentChar = potentialEvent.replace(":", "")
                continue

            #Kontrolle ob ein Wurf von einem nicht vorhandenen Charakter geworfen wurde
            if self.currentChar == "":
                continue

            # Korrektur für anderweitige Usernames
            self.currentChar = self.currentCharCorrection(self.currentChar)

            #Korrektur für "  ()" hinter einem Talent (vielleicht Spezwurf?)
            if " ()" in potentialEvent:
                potentialEvent = potentialEvent.replace(" ()", "")

            # Korrektur für falsche Talente
            potentialEvent = self.talentsCurrection(potentialEvent)

            #Prüfe ob Eigenschaftsprobe stattgefunden hat
            if self.validateTrait(potentialEvent):
                currentMod, currentSuccess, currentTaPZfP, currentTaWZfW = self.traitResult(chatlogLines[i+1].strip(), chatlogLines[i+2].strip())           
                self.traitsRolls.append([self.currentChar, "Eigenschaftsprobe", potentialEvent, self.traits[self.traitsLong.index(potentialEvent)], currentMod, currentSuccess, currentTaPZfP, currentTaWZfW])
                self.updateTraitUsage(self.currentChar, self.traits[self.traitsLong.index(potentialEvent)])
                continue

            # Prüfe ob Talent geworfen wurde
            if self.validateTalent(potentialEvent):
                category, trait1, trait2, trait3 = self.getTraits("talent", potentialEvent)

                # Ergebnis des Wurfs prüfen 
                currentMod, currentSuccess, currentTaP, currentTaW, currentTrait1, currentTrait2, currentTrait3 = self.talentResult(chatlogLines[i+1].strip(), chatlogLines[i+2].strip())
                self.talentsRolls.append([self.currentChar, category, potentialEvent, trait1, trait2, trait3, currentMod, currentSuccess, currentTaP, currentTaW, currentTrait1, currentTrait2, currentTrait3])
                self.updateTraitUsage(self.currentChar, [trait1, trait2, trait3])
                try:
                    self.updateTraitValues(self.currentChar, [trait1, trait2, trait3], [currentTrait1, currentTrait2, currentTrait3])
                except Exception as error:
                    print(error)
                    
                continue

            # Prüfe on Zauber geworfen wurde
            if self.validateSpell(potentialEvent):
                category, trait1, trait2, trait3 = self.getTraits("spell", potentialEvent)

                # Ergebnis des Wurfs prüfen
                currentMod, currentSuccess, currentZfP, currentZfW, currentTrait1, currentTrait2, currentTrait3 = self.spellResult(chatlogLines[i+1].strip(), chatlogLines[i+2].strip())    
                self.spellsRolls.append([self.currentChar, category, potentialEvent, trait1, trait2, trait3, currentMod, currentSuccess, currentZfP, currentZfW, currentTrait1, currentTrait2, currentTrait3])
                self.updateTraitUsage(self.currentChar, [trait1, trait2, trait3])
                self.updateTraitValues(self.currentChar, [trait1, trait2, trait3], [currentTrait1, currentTrait2, currentTrait3])
                continue

            # Prüfe Nahkampfangriff, Fernkampfangriff, Parade oder Ausweichmanöver
            if self.validateAttack(potentialEvent):
                thirdLine = chatlogLines[i+2].strip()
                if "Kampfgetümmel" in chatlogLines[i+2].strip():
                    thirdLine = chatlogLines[i+3].strip()

                #self.attackResult(chatlogLines[i+1].strip(), thirdLine)
                currentMod, currentSuccess, currentTaPZfP, currentTaWZfW = self.attackResult(chatlogLines[i+1].strip(), thirdLine)
                self.attacksRolls.append([self.currentChar, "Kampfprobe", potentialEvent, currentMod, currentSuccess, currentTaPZfP, currentTaWZfW])
                continue

            # Prüfe Initiativewurf
            if "Initiative" in potentialEvent and not "Initiativewurf" in potentialEvent and self.currentChar in potentialEvent:
                currentIni, rolledIni, currentMod = self.initativeResult(chatlogLines[i].strip(), chatlogLines[i+1].strip())
                self.initiativesRolls.append([self.currentChar, "Initiative", "Initiative", currentMod, rolledIni, currentIni])
                continue

            if "treffer" in potentialEvent:
                self.countDmg(chatlogLines[i+1].strip())
                continue


            # Prüfe Parade oder Ausweichmanöver

        # After processing all lines
        print(self.traitValues)
        try:
            self.writeTraitValues()
        except Exception as error:
            print(error)
        self.writeTraitUsageCounts()
        self.writeRollsToFile(self.traitsRolls, 'traits', f'{today}_traits_rolls.csv')
        self.writeRollsToFile(self.talentsRolls, 'talents', f'{today}_talents_rolls.csv')
        self.writeRollsToFile(self.spellsRolls, 'spells', f'{today}_spells_rolls.csv')
        self.writeRollsToFile(self.attacksRolls, 'attacks', f'{today}_attacks_rolls.csv')
        self.writeRollsToFile(self.initiativesRolls, 'initiative', f'{today}_initiatives_rolls.csv')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process DSA chatlogs.')
    parser.add_argument('chatlog_path', type=str, help='Path to the chatlog file')
    args = parser.parse_args()

    dsa_stats = DsaStats()
    chatlogLines = dsa_stats.process_chatlog(args.chatlog_path)
    dsa_stats.main(chatlogLines)