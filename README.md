# 🎬 QReel

**QReel** is a smart, AI-powered movie discovery app that blends classical search with a simulated **quantum search algorithm** to help you find the perfect movie — even if you barely remember it.

---

## 🔍 Problem

Movie enthusiasts and casual viewers often struggle with:
- Finding films based on vague memories or half-remembered plotlines
- Discovering truly similar movies beyond basic genre tags
- Accessing cast, soundtrack, and box office info all in one place

---

## 💡 Solution

QReel uses a hybrid approach combining **AI** and **quantum-inspired algorithms** to:

- Accept natural language queries (e.g., _"movie with dreams inside dreams"_ → Inception)
- Summarize user intent using OpenAI before querying TMDb
- Return rich film data: cast, trailer, soundtrack, box office, and iconic dialogue
- Recommend similar films using AI + scoring logic
- Support two modes: `classical_search` and `quantum_search`

---

## 🧠 AI-Enhanced Features

- ✨ **Natural Language Search**: Queries like "space movie with Matthew McConaughey" work perfectly
- 🧾 **Auto-Summarization**: AI filters and reformats vague user input into structured queries
- 🎼 **Soundtracks**: Pulled from Last.fm, with AI fallback if no result found
- 🎬 **Iconic Dialogues**: Generated using OpenAI from movie metadata
- 🎥 **Trailers & Cast**: Pulled via TMDb API
- 🧠 **Quantum vs Classical Toggle**: Compare search efficiency and diversity

---

## ⚙️ Tech Stack

- **Frontend**: React + TailwindCSS
- **Backend**: FastAPI (Python)
- **AI**: OpenAI GPT for query understanding & fallback generation
- **Quantum**: Simulated Grover-style quantum search logic
- **APIs**: 
  - [TMDb](https://www.themoviedb.org/)
  - [Last.fm](https://www.last.fm/api)

---

## 🧪 Search Modes

### Classical Search Logic

```python
def classical_search(movies: List[Dict[str, Any]], query: str) -> int:
    # Scores movies by matching query words with title/overview and adds popularity boost
```

### Quantum Search Logic (Simulated)

```python
def quantum_search(movies: List[Dict[str, Any]], query: str) -> int:
    # Amplifies most relevant movie with Grover-like iterations and simulates quantum tunneling
```

---

## 📊 Benefits

- **Faster** movie matching using quantum acceleration
- **Smarter** suggestions based on AI summarization
- **Richer** detail aggregation from multiple sources
- **Fun to Use**: Great for movie nerds, content creators, students, and casual watchers

---

## 🔐 Environment Setup

Create a `.env` file in the root of the backend project with the following keys:

```env
TMDB_API_KEY=your_tmdb_key_here
OPENAI_API_KEY=your_openai_key_here
LASTFM_API_KEY=your_lastfm_key_here
```

---

## 🧠 Who It's For

- Movie Fans 🎥  
- Cinephiles 🍿  
- Film Students 🎓  
- Content Creators 🎬  
- Anyone who forgets movie titles 😅  

---

## 🚀 Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/qreel.git
cd qreel

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Set up your .env file as shown above

# 4. Start the backend
uvicorn main:app --reload

# 5. In a new terminal, run the frontend
cd ../frontend
npm install
npm start
```

---

## 📦 Deployment

This project is deployable to AWS (frontend via S3+CloudFront, backend via Elastic Beanstalk or EC2). Subdomain recommended: `qreel.efraprojects.com`.

---

## 🧠 Future Ideas

- Real quantum integration with Qiskit
- User accounts + watchlists
- AI-powered reviews and critiques
- Multilingual subtitle matching

---

## 📸 Screenshot (Optional)

*Drop your UI screenshot here for visual appeal.*

---

## 🧑‍💻 Author

Built with love by [@EfraHdz-git](https://github.com/EfraHdz-git) – because smart movie search shouldn't be dumb.

---

## 📄 License

MIT – use it, fork it, break it, just give credit.
