import sys
import datetime
import string
import os
import re
import base64

# Listen, this ain't pretty, but for now it works.
# This is real code. It might not be ideal, but this is what peak performance looks like.
# Maybe moderate performance.
# Improve it if you want it's all open source for you to do whatever with.

def hasNumbers(str):
	return any(char.isdigit() for char in str)

def isNumber(word):
	test = word.replace("+", "").replace("-", "").replace("d", "")
	return all(char.isdigit() for char in test)

def getNumber(data):
	for word in data:
		if (isNumber(word)):
			return ensurePlus(processPrompts(word))
	return ""

def processPrompts(data, inside = False):
	global promptCount
	pipe = "|"
	brace = "}"
	if (inside):
		pipe = "&#124;"
		brace = "&#125;"

	regex = re.findall('((\d+)\?([^+\-]+)?)', data)
	for r in regex:
		value = r[1]
		name = r[2]
		if (name == ""):
			name = "Prompt"

		prompt = "?{%s%s%s%s%s[%s]" % (name, promptCount, pipe, value, brace, name.upper())
		promptCount += "&#8203;"
		data = data.replace(r[0], prompt)
	return data

def getWord(data, ignore = "", ignore2 = ""):
	for word in data:
		if (word != ignore and word != ignore2):
			if (isNumber(word)):
				continue
			else:
				return word
	return ""

def parseDamageType(data):
	if ("/" in data):
		return data.upper()
	else:
		return data.capitalize()

def ensurePlus(data):
	if ("d" in data):
		return data
	if ("-" in data):
		return data
	if ("+" not in data):
		return "+" + data
	return data

def increaseDie(data, amount = 1):
	if ("d" not in data):
		num = int(data)
		num *= amount
		return num

	split = data.split("d")
	numDice = int(split[0])
	numDice *= amount
	return "%sd%s" % (numDice, split[1])

def generatePrompt(defaultName, value, inside = False):
	if (promptInfo == ""):
		n = defaultName
	else:
		n = "%s (%s)" % (defaultName, promptInfo);

	if (configPrompts):
		if (inside):
			return "?{%s&#124;%s&#125;[%s]" % (n, str(value), defaultName.upper())
		else:
			return "?{%s|%s}[%s]" % (n, str(value), defaultName.upper())
	return "0"

def wrapDice(data):
	if ("d" in data):
		if (isNumber(data)):
			return "[[%s]]" % (data)
	return data

def processQuotes(data):
	regex = re.findall('(\"(.+?)\")', data)
	for r in regex:
		processed = r[0].replace(" ", "~~~~~")
		processed = processed.replace("\"", '')
		data = data.replace(r[0], processed)
	return data

def finishQuotes(data):
	return data.replace("~~~~~", " ")

def processDice(data):
	data = processPrompts(data)
	regex = re.findall("([0-9]+d?\S+|d+[0-9]\S+)", data);
	for r in regex:
		data = data.replace(r, "[[%s]]" % r)
	return data

if (len(sys.argv) > 1):
	infiles = [str(sys.argv[1])]
else:
	indir = os.path.dirname(os.path.realpath(__file__))
	infiles = os.listdir(indir)

keywordsDamage = ["p", "s", "p/s", "b", "bludgeoning", "piercing", "slashing", "acid", "cold", "electricity", "elec", "fire", "sonic", "force", "precision", "negative", "positive", "pos", "neg", "mental", "chaotic", "evil", "good", "lawful", "heal", "healing", "poison"]
keywordsAttack = ["melee", "ranged"]
keywordsHealing = ["pos", "positive", "healing", "heal"]

saveTypes = ["fort", "ref", "will"]
saveFullTypes = ["fortitude", "reflex", "will"]
abilityTypes = ["str", "dex", "con", "int", "wis", "cha"]
abilityFullTypes = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
skillTypes = ["perception", "acrobatics", "arcana", "athletics", "crafting", "deception", "diplomacy", "intimidation", "medicine", "nature", "occultism", "performance", "religion", "society", "stealth", "survival", "thievery"]

for infile in infiles:
	if (infile.startswith("_")):
		continue
	if (not infile.endswith(".txt")):
		continue
	with open(infile, 'r') as file:
		configPrompts = True
		configImage = ""
		configTitles = True
		configName = ""
		configGmInit = False
		configCharMaker = False;

		contents = "\n%s" % (file.read())

		data = contents.split("\n>")
		macroOut = "# Generating macros from %s %s.\n\n" % (file.name, datetime.datetime.now())
		macroCount = 0;

		charMakerOut = "";
		hp = "";
		ac = "";
		tac = "";
		speed = "";

		for d in data:
			lines = d.strip(">").split("\n")

			skills = "?{Skill"
			inits = "?{Initiative"
			secretskills = "?{Skill"
			abilities = "?{Ability"
			saves = "?{Save"

			damage = ""
			crit = ""
			footer = ""		
			comment = ""
			canCrit = False
			isSkill = False
			isInit = False
			isAbility = False
			isSave = False
			isDamage = True
			isFatal = False;
			deadly = ""
			hasTitle = False
			damageLabel = "damage"
			blanks = ""
			bullets = "&bull;"
			promptInfo = ""
			preMacroNote = ""
			gmNotes = ""
			macroId = ""
			macro = ""
			promptCount = ""
			

			for line in lines:
				if (line == ""):
					continue

				if (line[0] == "#"):
					continue

				linedata = line.split("#")[0].strip();

				if (linedata.startswith("character:")):
					configName = linedata.split(":", 1)[1].strip()
					configCharMaker = True
					continue
				if (linedata.startswith("config:")):
					commandline = linedata.split(":", 1)[1]
					commandsplit = commandline.split("=")
					command = commandsplit[0].strip()
					setting = commandsplit[1].strip()
					if (command == "prompts"):
						if (setting == "off"):
							configPrompts = False
						if (setting == "on"):
							configPrompts = True
					if (command == "header"):
						configImage = "[Header](%s)&#13;" % (setting)
					if (command == "titles"):
						if (setting == "off"):
							configTitles = False
						if (setting == "on"):
							configTitles = True
					if (command == "name"):
						configName = "%s " % (setting)
					if (command == "gminit"):
						if (setting == "off"):
							configGmInit = False
						if (setting == "on"):
							configGmInit = True
					if (command == "charmaker"):
						if (setting == "off"):
							configCharMaker = False
						if (setting == "on"):
							configCharMaker = True
					continue

				if (linedata.startswith("*")):
					footer += "{{%s=*%s*}} " % (bullets, linedata.strip("*").strip())
					bullets += "&#8203;"
					continue

				if (linedata.startswith("?")):
					promptInfo = linedata.split(" ", 1)[1].strip()
					continue

				if (linedata.startswith(".")):
					preMacroNote = "&bull; %s \n" % linedata.split(" ", 1)[1].strip()
					continue

				if (linedata.startswith("%")):
					gmNotes += "\n/w gm &bull; ``%s``" % linedata.split(" ", 1)[1].strip()
					continue

				if (not hasTitle):
					title = ""

					if (".jpg" in linedata or ".png" in linedata or ".gif" in linedata):
						imageUrl = re.search("(?P<url>https?://[^\s]+)", linedata).group("url")
						title += "[Header](%s)&#13;" % (imageUrl)

					if (configTitles):
						stripUrl = re.sub(r'http\S+', '', linedata).strip()
						title += "%s - **%s**" % (configName, string.capwords(stripUrl))

					titleCode = linedata.upper().strip()

					macroId = stripUrl.upper()
					macro += "&{template:default} {{name=%s%s}} " % (configImage, title)

					hasTitle = True
					continue

				if (".jpg" in linedata or ".png" in linedata or ".gif" in linedata):
					macro += "{{%s=[x](%s)}}" % (blanks, linedata)
					blanks += "&#8203;"
					continue;

				if (":" in linedata):
					split = linedata.split(":")
					rightside = processQuotes(split[1])
					words = rightside.split(" ")
					output = ""
					for word in words:
						output += processDice(word) + " "
					output = finishQuotes(output)

					footer += "{{%s=%s}}" % (split[0].capitalize().strip(), output.strip())
					continue

				words = linedata.strip().split(" ")

				intersect = set(keywordsAttack).intersection(set(words))
				if (len(intersect) > 0):
					attackType = intersect.pop()
					canCrit = True

					mapenalty = "?{MAP|0|-5|-10}[MAP]"
					if ("agile" in words):
						mapenalty = "?{MAP|0|-4|-8}[MAP]"

					info = ""
					if ("touch" in words):
						info += "Touch "

					hitBonus = getNumber(words)

					macro += "{{%s=[[d20%s[HIT]+%s+%s]] %s}} " % (attackType, hitBonus, mapenalty, generatePrompt("Hit Bonus", 0), info.strip())

				if ("range" in words):
					macro += "{{range=%s}} " % (string.capwords(linedata.split(" ", 1)[1]))

				if ("sneak" in words):
					footer += "{{Sneak Attack=[[%s]]}} " % (getNumber(words))

				if ("save" in words):
					footer += "{{Save=%s %s}} " % (getWord(words, "save").capitalize(), getNumber(words).strip("+"))

				if ("deadly" in words):
					deadly += " [[%s]] Deadly" % (getNumber(words))

				if ("heighten" in words):
					times = 1
 
					macroLabel = "Heighten"
					if ("persist" in words):
						macroLabel = "Hgt Persist"

					# parse level+increment part, the remove this token so it doesn't get confused with dmg
					level, step = [int(token) for token in words[0].split("+")]
					words = words[1:]
 
					macroLabel += " %s+" % level
 
					heighten = getNumber(words)
					heightenMacro = "?{%s|0," % (macroLabel)
					for x in range(step, 11, step):
						number = increaseDie(heighten, times)
						secondNumber = number
						if ("persist" in words):
							secondNumber = "**%s**" % (number)
 
						heightenMacro += "|%s (+%s),%s" % (x, number, secondNumber)
						times += 1
 
					if ("persist" in words):
						footer += "{{Heightened&#8203;=+%s} %s}}" % (heightenMacro, getWord(words, "heighten+1", "persist").capitalize())
					else:
						footer += "{{Heightened=[[%s}]] %s}}" % (heightenMacro, getWord(words, "heighten+1").capitalize())
 
				elif ("persist" in words): # Sorry
					footer += "{{Persist=**%s** %s}} " % (getNumber(words), parseDamageType(getWord(words, "persist")))
				elif ("extra" in words):
					footer += "{{Extra Damage=[[%s]] %s}} " % (getNumber(words), parseDamageType(getWord(words, "extra")))
				elif ("crit" in words):
					isFatal = True;
					crit += "[[%s+%s]] %s " % (getNumber(words), damagePrompt, damageType)

				else: # But it works!
					intersect = set(keywordsDamage).intersection(set(words))

					if (len(intersect) > 0):
						damageType = parseDamageType(intersect.pop())
						damagePrompt = generatePrompt("%s Bonus" % (damageType), 0)
						damage += "[[%s+%s]] %s " % (getNumber(words), damagePrompt, damageType)
						if (damageType.lower() in keywordsHealing):
							damageLabel = "Healing"
							canCrit = False

				if (titleCode == "SKILLS"):
					isSkill = True
					isDamage = False

					skillSplit = re.split('(\d+)',linedata)
					skillName = string.capwords(skillSplit[0].strip("+").strip("-").strip())

					skillNameLabel = skillName
					if (skillName == "Other"):
						skillNameLabel = "?{Skill Name&#124;Other&#125;"

					# Use &#125; instead of } when doing this for reasons, but only sometimes use &#125;
					skills += "|%s (%s),{{%s=[[d20%s+%s]]&#125;&#125;" % (skillName, getNumber(words), skillNameLabel, getNumber(words), generatePrompt("%s Bonus" % (skillName), 0, True))
					inits += "|%s (%s),{{%s=[[d20%s+%s &{tracker&#125;]]&#125;&#125;" % (skillName, getNumber(words), skillName, getNumber(words), generatePrompt("Initiative Bonus", 0, True))

					skillroll = "[[d20%s+%s]]" % (getNumber(words), generatePrompt("%s Bonus" % (skillName), 0, True))
					# secretskills += "|%s (%s),{{%s=%s %s %s %s&#125;&#125;" % (skillName, getNumber(words), skillNameLabel, skillroll, skillroll, skillroll, skillroll)
					secretskills += "|%s (%s),{{%s=[?](%s)&#125;&#125;" % (skillName, getNumber(words), skillNameLabel, skillroll)

				if (titleCode == "ABILITY"):
					isAbility = True
					isDamage = False

					if (len(words) == 6):
						scores = words.copy()
						parseIndex = 0;

						for score in scores:
							label = abilityFullTypes[parseIndex].capitalize();
							abilities += "|%s (%s),{{%s=[[d20%s+%s]]&#125;&#125;" % (label, ensurePlus(score), label, ensurePlus(score), generatePrompt("%s Bonus" % (label), 0, True))
							parseIndex += 1
						continue

					label = string.capwords(getWord(words))
					if (label == ""):
						label = abilityFullTypes[parseIndex].capitalize()

					abilities += "|%s (%s),{{%s=[[d20%s+%s]]&#125;&#125;" % (label, getNumber(words), label, getNumber(words), generatePrompt("%s Bonus" % (label), 0, True))
					
				if (titleCode == "SAVES"):
					isSave = True
					isDamage = False

					if (len(words) == 3):
						scores = words.copy()
						parseIndex = 0;

						for score in scores:
							label = saveFullTypes[parseIndex].capitalize();
							saves += "|%s (%s),{{%s=[[d20%s+%s]]&#125;&#125;" % (label, ensurePlus(score), label, ensurePlus(score), generatePrompt("%s Bonus" % (label), 0, True))
							parseIndex += 1
						continue

					label = string.capwords(getWord(words))
					if (label == ""):
						label = saveFullTypes[parseIndex].capitalize()

					saves += "|%s (%s),{{%s=[[d20%s+%s]]&#125;&#125;" % (label, getNumber(words), label, getNumber(words), generatePrompt("%s Bonus" % (label), 0, True))

				if (titleCode == "STATS"):
					parseIndex = 0
					isDamage = False
					stats = "?{Stats"

					for score in words:
						if (parseIndex < 6):
							label = abilityFullTypes[parseIndex].capitalize();
							stats += "|%s (%s),{{%s=[[d20%s+%s]]&#125;&#125;" % (label, ensurePlus(score), label, ensurePlus(score), generatePrompt("%s Bonus" % (label), 0, True))

						elif (parseIndex == 6):
							ac = score

						elif (parseIndex == 7):
							tac = score

						elif (parseIndex < 11):
							label = saveFullTypes[parseIndex - 8].capitalize();
							stats += "|%s (%s),{{%s=[[d20%s+%s]]&#125;&#125;" % (label, ensurePlus(score), label, ensurePlus(score), generatePrompt("%s Bonus" % (label), 0, True))

						elif (parseIndex == 11):
							hp = score
						elif (parseIndex == 12):
							speed = score

						parseIndex += 1

					macro += stats + "}";


			if (isDamage):
				if (damage.strip() != ""):
					macro += "{{%s=%s}} " % (damageLabel, damage.strip())

			if (canCrit):
				if (damage.strip() != ""):
					if (isFatal):
						macro += "{{critical=%s%s}} " % (crit.strip(), deadly)
					else:
						macro += "{{critical=%s%s}} " % (damage.strip(), deadly)
			
			if (isSkill):
				macro += "%s}" % (skills)

			if (isAbility):
				macro += "%s}" % (abilities)

			if (isSave):
				macro += "%s}" % (saves)

			macro += footer.strip()
			macro = macro.strip()

			macroCount += 1

			# Repeat Skills to generate Initiative macro
			if (isSkill):
				gmInit = ""
				if (configGmInit):
					gmInit = "/w gm "

				macro += "\n\nINITIATIVE (GENERATED FROM SKILLS)\n%s&{template:default} {{name=%s - **Initiative**}} %s}" % (gmInit, configName, inits)
				macroCount += 1

				macro += "\n\nSECRET SKILL CHECK (GENERATED FROM SKILLS)\n/w gm &{template:default} {{name=%s - **Secret Skills**}} %s}" % (configName, secretskills)

			# Clear the prompt info
			promptInfo = ""

			if (macroId != ""):
				macroOut += macroId + "\n" + preMacroNote + macro + gmNotes + "\n\n"
				if (configCharMaker):
					toEncode = preMacroNote + macro + gmNotes;
					encoded = base64.b64encode(bytes(toEncode, 'utf-8')).decode('utf-8');
					charMakerOut += "--ability " + macroId + " >> " + encoded + " ";

			# for d in data

		macroOut += "# %s Macros generated." % (macroCount)
		macroOut += "\n# Created by Roll20 Macro Generator (Pathfinder Playtest)"
		macroOut += "\n# https://github.com/kylepulver/roll20-macro-generator"

		outfile = open("_%s-macros.txt" % (infile.split(".")[0]), "w")
		outfile.write(macroOut.strip())
		outfile.close()

		if (charMakerOut != ""):
			charMakerOut = "!make --name " + configName + " --hp " + hp + " --ac " + ac + " --tac " + tac + " --speed " + speed + " " + charMakerOut;
			outfile = open("__%s-char.txt" % (infile.split(".")[0]), "w")
			outfile.write(charMakerOut.strip());
			outfile.close();
