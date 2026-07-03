# Calibr — Weights Validation Notes

## Gold set: Day 8 (5 candidates, 1 JD)

**JD:** Backend Engineer, 2-4 years experience (Python, FastAPI, PostgreSQL,
Redis, Docker, Kubernetes, AWS, REST API, Microservices)

**Weights tested:** w1_skill=0.45, w2_semantic=0.35, w3_experience=0.20

## Results

| Rank | Candidate | Score | Manual Label | Agreement |
|------|-----------|-------|--------------|-----------|
| 1 | Candidate A — Strong all-round fit | 77.57 | good | ✅ |
| 2 | Candidate B — Right skills, short experience | 53.90 | medium | ✅ |
| 3 | Candidate D — Partial match, some relevant skills | 49.16 | medium | ✅ |
| 4 | Candidate C — Wrong tech stack, good experience | 23.56 | poor | ✅ |
| 5 | Candidate E — No relevant skills or experience | 17.92 | poor | ✅ |

**Agreement rate: 5/5 (100%)**

## Key observations

1. Formula rankings matched manual labels exactly — no weight adjustment
   needed based on this gold set.

2. Candidate C had significantly more experience (36 months) than
   Candidate D (17 months), but ranked lower because their entire tech
   stack (Java, Spring Boot, MySQL) was irrelevant to the JD. The
   skill signal (0.0 for C vs 33.3 for D) correctly dominated, showing
   the w1=0.45 weight for skill match is working as intended.

3. Semantic similarity gave Candidate C a 46.8 even with zero skill
   match — suggesting the semantic signal alone can be overly generous
   to mismatched candidates. This is why skill match is weighted
   highest (0.45) rather than relying on semantic similarity alone.

## Weight adjustment decision

**No adjustment made.** Starting weights (0.45 / 0.35 / 0.20) produce
correct rankings on this gold set.

Will expand to 50+ labeled examples across multiple JDs on Day 10-11
to stress-test further.

## What I'd adjust if rankings had been wrong

- If C had ranked above D (experience over-weighted): reduce w3 below 0.20
- If B had ranked above A (semantic over-weighted vs skill): reduce w2,
  increase w1
- If E had ranked above C (semantic too generous): increase w1 weight
  to dominate over soft semantic matches