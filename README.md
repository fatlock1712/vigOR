#vigOR — Health Routing Agent
# 🌲 BeaverHacks 2026 Submission
# Track: NVIDIA — Best use of Nemotron
# Theme: Public Health & Environmental Safety

## 💡 Inspiration
_Asthma_ is a leading cause of preventable death in the US. In Oregon, the crisis is particularly acute: the state suffers from an asthma death rate nearly double the national average, despite making up only 1.27% of the population. Research shows that early notification of air quality triggers can save thousands of lives. 
vigOR was built to turn this data into a shield, giving people an information advantage over their environment.

## 🚀 What it does

**Feature 1:** Nemotron-Powered Route AnalysisThe core "Smart Route Analyzer" evaluates multiple paths based on transport mode. It samples environmental data points (AQI, pollen, weather) along each route, converts them into high-context JSON, and feeds them into NVIDIA Nemotron. The AI then acts as a medical expert, deciding if a user should "Go" or "Wait" based on their specific health profile.

**Feature 2:** Real-time Air Quality MeshIntegrated live sensor data providing block-level AQI alerts. Users can visualize environmental hazards in Oregon and beyond in real-time.

**Feature 3:** Nemotron AI CompanionA 24/7 health agent that understands user intent. Beyond routes, users can chat with Nemtron to get personalized health suggestions, weather forecasts, and advice on managing asthma triggers.

## 🛠️ How we built it

**Frontend:** A "Cyber-Medical" HUD built with HTML5, CSS3 (Custom Properties), and Vanilla JavaScript. We focused on a high-tech, low-friction UI inspired by modern aerospace and automotive interfaces.

**Backend:** Python powered by Flask and FastAPI to handle complex asynchronous requests.

**AI Engine:** NVIDIA Nemotron integrated via specialized prompting to act as a diagnostic and routing agent.

**Database:** Google Firebase for secure user authentication and encrypted health records.

**APIs/Tools:** Google Routes API, Pollen API, Air Quality API, Maps JavaScript API, and Geocoding API.

## 🧠 Challenges we ran into
Initially, we struggled to find a dataset comprehensive enough to build a traditional ML model for environmental safety. We pivoted to a Generative AI Agent approach using Nemotron. By feeding real-time API data into Nemotron with specific medical logic, we were able to create a far more flexible and personalized safety evaluator than a static model could ever provide.

## 🏅 Accomplishments that we're proud of
_The Agentic Workflow:_ Successfully building an AI Agent that doesn't just chat, but actually fetches data, analyzes coordinates, and makes safety decisions.

_Zero-Trust Concept:_ Designing a database structure intended for high-security medical record storage.

_UI/UX:_ Crafting a "Tesla-inspired" minimalist aesthetic that makes complex health data easy to digest at a glance.

## 📖 What we learned
We pushed beyond our classroom knowledge to learn using many new technologies, tools.

* **Loc - Project Lead | ML/AI & Full-stack**
  * How to use Flask to connect Python to HTML.
  * How to access a Database from HTML.
  * How to prompt engineer to make Nemotron act as a medical route analyst.
* **Alex: - WIP**
  *
  * 
  *
* **Brian - WIP**
  *
  * 
  *
* **Kalvin: - WIP**
  *
  * 
  *
## 🔮 What's next for vigOR
_Mobile Deployment:_ Transforming the web platform into a native app for real-time, on-the-go GPS alerts.

_Wearable Integration:_ Pumping live heart rate and $O_2$ saturation data directly into Nemotron for even more precise risk assessments.

_Community Scaling:_ Partnering with local health organizations to provide sponsored, life-saving equipment suggestions (like inhaler spacers or HEPA filters) based on user needs.
