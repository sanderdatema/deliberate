# Phase 19: Pool Expansion — Research Results

## Design Decisions

- Pool groeit van 25 naar 54 personas (niemand gaat weg)
- Gender: 23F / 28M / 3N (43% / 52% / 5%)
- Geen "code" vs "general" categorisering — experts uit alle domeinen
- Persona's krijgen `domains` veld voor intake matching
- Intake agent selecteert het beste team per vraag (geen template)
- Genderbalans als selectiecriterium bij teamselectie
- Alles in een keer implementeren

## Huidige Pool (25, ongewijzigd)

| Naam | Gender | Domein | Status |
|------|--------|--------|--------|
| Socrates | M | Dialectisch doorvragen | Bestaand |
| William of Occam | M | Eenvoud/parsimonie | Bestaand |
| Leonardo da Vinci | M | Interdisciplinair/visueel denken | Bestaand |
| Sherlock Holmes | M | Deductief redeneren (fictief) | Bestaand |
| Machiavelli | M | Strategisch realisme/machtsdynamiek | Bestaand |
| Knights Templar | N | Plicht/missie (archetype) | Bestaand |
| Harriet Tubman | F | Bevrijding/escape routes | Bestaand |
| Simone Weil | F | Lijden/rechtvaardigheid | Bestaand |
| Miss Marple | F | Patronen uit het alledaagse (fictief) | Bestaand |
| Emmy Noether | F | Wiskundige symmetrie | Bestaand |
| Ibn Khaldun | M | Beschavingscycli/historiografie | Bestaand |
| Karl Marx | M | Systeemkritiek/klasse-analyse | Bestaand |
| Georg Hegel | M | Dialectische synthese | Bestaand |
| Hannah Arendt | F | Politieke filosofie | Bestaand |
| De Samenvatter | N | Concrete vertaling (functioneel) | Bestaand |
| Linus Torvalds | M | Code quality/directheid | Bestaand |
| Kent Beck | M | TDD/eenvoud | Bestaand |
| Martin Fowler | M | Architectuur/refactoring | Bestaand |
| Bruce Schneier | M | Security | Bestaand |
| Steve Jobs | M | Productvisie | Bestaand |
| Don Norman | M | UX/cognitief design | Bestaand |
| Jony Ive | M | Design craft/esthetiek | Bestaand |
| Donald Knuth | M | Algoritmische performance | Bestaand |
| Grace Hopper | F | Pragmatisme/debugging | Bestaand |
| Code Synthesizer | N | Code synthese (functioneel) | Bestaand |

## Nieuwe Personas (29)

### Vrouwen (14)

| Naam | Domein | Kernvraag |
|------|--------|-----------|
| Joan Clarke | Probabilistische inferentie onder onzekerheid | "Welke zekerheid hebben we echt, en wat kunnen we uitsluiten?" |
| Margaret Hamilton | Failure-mode engineering | "Wat gebeurt er als dit breekt?" |
| Barbara Liskov | Abstractie/contracttheorie (LSP) | "Houdt dit zich aan zijn contract, of alleen aan de naam?" |
| Hedy Lamarr | Cross-domein analogisch uitvinden | "Welk mechanisme uit een ander veld lost dit op?" |
| Ada Lovelace | Algoritmisch denken | "Wat is het fundamentele rekenproces hier?" |
| Lynn Conway | Democratisering van complexe systemen | "Wie kan dit daadwerkelijk implementeren?" |
| Radia Perlman | Zelforganiserende fouttolerante systemen | "Werkt dit nog als de gebruiker fouten maakt?" |
| Frances Allen | Compilertransformatie | "Wat berekent dit argument eigenlijk, en is er een efficienter pad?" |
| Maryam Mirzakhani | Verborgen equivalenties tussen domeinen | "Is dit probleem al opgelost in een ander domein?" |
| Katherine Johnson | Precisie als morele verplichting | "Wat is de wortel van deze bewering?" |
| Donella Meadows | Feedback, hefboompunten, systeemgedrag | "Welke feedbackstructuur produceert dit gedrag?" |
| Elinor Ostrom | Commons governance, lokaal zelfbestuur | "Hebben de mensen die dit raakt al een werkende oplossing?" |
| Cecilia Payne-Gaposchkin | Bewijs vs autoriteit | "Wordt dit verworpen op basis van bewijs of op basis van autoriteit?" |
| Virginia Apgar | Operationaliseerbare meting | "Hoe maken we dit oordeel meetbaar en reproduceerbaar?" |

### Mannen (10)

| Naam | Domein | Kernvraag |
|------|--------|-----------|
| Alan Turing | Formeel redeneren, beslisbaarheid | "Is dit probleem in principe oplosbaar?" |
| Daniel Kahneman | Cognitieve bias, System 1/2 | "Welke bias produceert deze consensus?" |
| Nassim Taleb | Antifragiliteit, staartrisico | "Als dit misgaat, gaat het dan een beetje of catastrofaal mis?" |
| Thorbecke | Constitutioneel recht, institutioneel ontwerp | "Overleeft dit voorstel een regeringswissel?" |
| Shakespeare | Taal als macht, menselijke motivatie | "Wie heeft baat bij dit verhaal zo verteld?" |
| Aristoteles | Categorisering, deugdethiek, phronesis | "Wat voor soort ding is dit, en welke maatstaf hoort daarbij?" |
| Cicero | Retorische architectuur, overtuigingskracht | "Is dit argument in de juiste volgorde opgebouwd?" |
| John Rawls | Rechtvaardigheid, veil of ignorance | "Zou je dit accepteren als je niet wist welke positie je inneemt?" |
| Buckminster Fuller | Whole-system design, synergetics | "Lossen we het symptoom op of redesignen we het systeem?" |
| Arsene Lupin | Lateraal denken, constraint-inversie (fictief) | "Welke aanname maakt iedereen hier die niet klopt?" |

### Literaire karakters (5)

| Naam | Gender | Domein | Kernvraag |
|------|--------|--------|-----------|
| Odysseus | M | Situationele intelligentie, strategisch geduld | "Waar zit het verborgen hefboommoment?" |
| Scheherazade | F | Narratieve intelligentie, framing | "Welk verhaal maakt de beste oplossing vanzelfsprekend?" |
| Portia | F | Regels vs rechtvaardigheid | "Leidt de logica hier tot een rechtvaardig resultaat?" |
| Atticus Finch | M | Empathische morele moed | "Hoe ziet dit eruit vanuit het perspectief van de ander?" |
| Elizabeth Bennet | F | Sociale intelligentie, metacognitie | "Welke sociale dynamiek stuurt dit gesprek onzichtbaar?" |

## Expertise Matrix

| Domein | Persona's |
|--------|-----------|
| Psychologie & gedrag | Kahneman, Shakespeare, Elizabeth Bennet |
| Economie & risico | Taleb, Ostrom, Aristoteles |
| Governance & recht | Thorbecke, Rawls, Portia, Arendt |
| Communicatie & retoriek | Shakespeare, Scheherazade, Cicero |
| Systeemdenken | Meadows, Fuller, Ibn Khaldun |
| Formeel/logisch | Turing, Noether, Socrates, Occam |
| Code & architectuur | Linus, Beck, Fowler, Hamilton, Liskov, Allen, Conway, Knuth |
| Security & crypto | Schneier, Clarke, Turing |
| Design & creativiteit | Da Vinci, Jobs, Ive, Norman, Lamarr |
| Lateraal/creatief | Lupin, Odysseus, Lamarr, Mirzakhani |
| Moreel/ethisch | Atticus Finch, Weil, Tubman, Arendt, Rawls |
| Precisie & meten | Katherine Johnson, Apgar, Knuth, Hopper |
| Anti-groepsdenken | Payne-Gaposchkin, Taleb, Kahneman |
| Institutioneel | Thorbecke, Ostrom, Rawls |

## Genderverdeling

| | F | M | N | Totaal |
|---|---|---|---|--------|
| Bestaand | 5 | 15 | 3 | 23+2fn |
| Nieuw | 18 | 13 | 0 | 31 |
| **Totaal** | **23** | **28** | **3** | **54** |
| **%** | **43%** | **52%** | **5%** | |

## Bronnen

Research uitgevoerd op 2026-03-22 door drie parallelle agents:
- Vrouwelijke experts: Joan Clarke t/m Virginia Apgar (14 candidates)
- Mannelijke experts: Kahneman t/m Cicero (10 candidates)
- Literaire karakters: Odysseus t/m Elizabeth Bennet (5 candidates)

Volledige research transcripten beschikbaar in agent output files.

---
*Research completed: 2026-03-22*
*For use in Phase 19 PLAN creation*
