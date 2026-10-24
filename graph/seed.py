"""Seed a realistic one day conference into the Hallway graph.

The data is clearly sample data in the spirit of GitHub Universe: agent and
developer tooling talks, MCP everywhere. It exists so every query, agent and
demo step runs end to end before the real schedule is ingested by Scout.

Graph name comes from HALLWAY_GRAPH (default "hallway"). Tests pass their own
graph object pointing at a scratch graph.
"""

import os
from pathlib import Path

from falkordb import FalkorDB

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

TOPICS = [
    "MCP",
    "AI Agents",
    "Rust",
    "Developer Tools",
    "Open Source",
    "Agent Memory",
    "Web Data",
    "Code Review",
    "Security",
]

ROOMS = ["Main Stage", "Workshop 1", "Workshop 2"]

# id, name, kind, company, handle
PEOPLE = [
    ("rene", "Rene Turcios", "attendee", "CloudCorpRecords", "@cloudtheboy"),
    ("maya-chen", "Maya Chen", "speaker", "GitHub", "@mayachen"),
    ("diego-fuentes", "Diego Fuentes", "speaker", "Independent", "@diegof"),
    ("priya-nair", "Priya Nair", "speaker", "FalkorDB", "@priyacodes"),
    ("sam-okafor", "Sam Okafor", "speaker", "SustainOSS", "@samok"),
    ("lena-fischer", "Lena Fischer", "speaker", "GitHub", "@lenaf"),
    ("ken-watanabe", "Ken Watanabe", "speaker", "DevTools Weekly", "@kenw"),
    ("rosa-jimenez", "Rosa Jimenez", "speaker", "Bright Data", "@rosaj"),
    ("tom-alvarez", "Tom Alvarez", "speaker", "ReviewBot", "@tomalv"),
    ("alex-rivera", "Alex Rivera", "attendee", "Independent", "@alexr"),
    ("jordan-lee", "Jordan Lee", "attendee", "Stealth Startup", "@jordanl"),
    ("nina-petrova", "Nina Petrova", "speaker", "JetBrains", "@ninap"),
    ("marcus-webb", "Marcus Webb", "speaker", "OpenAI", "@marcusw"),
    ("aiko-tanaka", "Aiko Tanaka", "speaker", "Vercel", "@aikot"),
    ("omar-haddad", "Omar Haddad", "speaker", "Lockstep Security", "@omarh"),
    ("grace-muli", "Grace Muli", "attendee", "Andela", "@gracem"),
    ("ben-kowalski", "Ben Kowalski", "attendee", "Independent", "@benk"),
    ("zoe-laurent", "Zoe Laurent", "speaker", "PipeDream Labs", "@zoel"),
]

# person_id, topic, weight (1 to 3)
INTERESTS = [
    ("rene", "MCP", 3),
    ("rene", "AI Agents", 3),
    ("rene", "Developer Tools", 2),
    ("rene", "Rust", 2),
    ("maya-chen", "MCP", 3),
    ("maya-chen", "Agent Memory", 2),
    ("diego-fuentes", "Rust", 3),
    ("diego-fuentes", "Developer Tools", 2),
    ("priya-nair", "AI Agents", 3),
    ("priya-nair", "Agent Memory", 3),
    ("priya-nair", "Rust", 1),
    ("sam-okafor", "Open Source", 3),
    ("sam-okafor", "Developer Tools", 1),
    ("lena-fischer", "Open Source", 2),
    ("lena-fischer", "MCP", 2),
    ("lena-fischer", "AI Agents", 1),
    ("ken-watanabe", "Developer Tools", 3),
    ("ken-watanabe", "MCP", 1),
    ("rosa-jimenez", "Web Data", 3),
    ("rosa-jimenez", "Developer Tools", 1),
    ("rosa-jimenez", "AI Agents", 1),
    ("tom-alvarez", "Code Review", 3),
    ("tom-alvarez", "AI Agents", 2),
    ("tom-alvarez", "MCP", 1),
    ("alex-rivera", "MCP", 2),
    ("alex-rivera", "Rust", 3),
    ("alex-rivera", "Developer Tools", 1),
    ("jordan-lee", "AI Agents", 2),
    ("jordan-lee", "Web Data", 2),
    ("jordan-lee", "MCP", 1),
    ("nina-petrova", "Developer Tools", 3),
    ("nina-petrova", "Rust", 2),
    ("marcus-webb", "AI Agents", 3),
    ("marcus-webb", "MCP", 2),
    ("aiko-tanaka", "Developer Tools", 3),
    ("aiko-tanaka", "Web Data", 2),
    ("omar-haddad", "Security", 3),
    ("omar-haddad", "MCP", 2),
    ("grace-muli", "AI Agents", 2),
    ("grace-muli", "Open Source", 2),
    ("ben-kowalski", "Rust", 3),
    ("ben-kowalski", "Open Source", 1),
    ("zoe-laurent", "Web Data", 3),
    ("zoe-laurent", "AI Agents", 2),
]

# id, title, starts, ends, room, [speaker ids], [topics], blurb
TALKS = [
    ("t0", "Opening Keynote: Software in the Agent Era", "09:00", "09:30",
     "Main Stage", ["marcus-webb"],
     ["AI Agents", "MCP", "Developer Tools", "Open Source"],
     "The talk everyone puts on their list: where agent tooling goes next, "
     "in plain terms."),
    ("t1", "MCP in Production: Tool Servers That Scale", "09:30", "10:15",
     "Main Stage", ["maya-chen"], ["MCP", "AI Agents"],
     "What breaks when a thousand agents hit your MCP server at once."),
    ("t2", "Rust CLIs That Feel Instant", "09:30", "10:15",
     "Workshop 1", ["diego-fuentes"], ["Rust", "Developer Tools"],
     "Startup time budgets and the profiling habits that keep CLIs fast."),
    ("t3", "Agents That Remember", "10:30", "11:15",
     "Main Stage", ["priya-nair"], ["AI Agents", "Agent Memory"],
     "Memory architectures for agents that survive across sessions."),
    ("t13", "What Breaks at Scale: A War Stories Panel", "10:30", "11:15",
     "Workshop 2", ["nina-petrova", "omar-haddad"],
     ["Developer Tools", "Security"],
     "Two builders trade outage stories and the checks that would have "
     "caught them."),
    ("t4", "Keeping Open Source Sustainable", "11:15", "12:00",
     "Workshop 2", ["sam-okafor", "lena-fischer"], ["Open Source"],
     "Funding, burnout, and governance, from two maintainers."),
    ("t5", "Dev Tools Lightning Round", "11:15", "12:00",
     "Workshop 1", ["ken-watanabe"], ["Developer Tools"],
     "Eight tools, five minutes each, no slides over two lines."),
    ("t14", "Docs That Write Themselves", "12:00", "12:45",
     "Workshop 1", ["aiko-tanaka"], ["Developer Tools", "Web Data"],
     "Pipelines that keep documentation honest by reading the product, "
     "not the tickets."),
    ("t6", "Graph Memory for Multi-Agent Systems", "13:00", "13:45",
     "Main Stage", ["maya-chen"], ["Agent Memory", "AI Agents"],
     "One shared graph as the hand-off layer between cooperating agents."),
    ("t7", "Scraping the Modern Web Without Tears", "13:00", "13:45",
     "Workshop 1", ["rosa-jimenez"], ["Web Data", "Developer Tools"],
     "Live data from sites that fight back, without the proxy farm."),
    ("t15", "MCP Security Deep Dive", "14:00", "14:45",
     "Main Stage", ["omar-haddad"], ["MCP", "Security"],
     "Threat models for tool servers: confused deputies, scope creep, "
     "and audit gaps."),
    ("t8", "Code Review in the Age of Agents", "14:00", "14:45",
     "Workshop 2", ["tom-alvarez"], ["Code Review", "AI Agents"],
     "When half your PRs are agent written, review has to change."),
    ("t9", "Shipping Secure MCP Servers", "14:45", "15:30",
     "Main Stage", ["lena-fischer"], ["MCP", "Security"],
     "Auth, scoping, and audit trails for tool servers in production."),
    ("t10", "From Prototype to Production Agents", "15:30", "16:15",
     "Workshop 1", ["diego-fuentes"], ["AI Agents", "Rust"],
     "The unglamorous 90 percent: retries, evals, and cost control."),
    ("t16", "Rust in the Browser: WASM Tooling", "15:30", "16:15",
     "Workshop 2", ["nina-petrova"], ["Rust", "Developer Tools"],
     "Shipping Rust to the browser without the tears: bundles, "
     "debugging, and interop."),
    ("t11", "Evaluating Agents in the Wild", "16:15", "17:00",
     "Main Stage", ["priya-nair"], ["AI Agents", "Agent Memory"],
     "Golden cases, incident suites, and knowing when your agent regressed."),
    ("t17", "Data Pipelines for Agent Builders", "16:15", "17:00",
     "Workshop 2", ["zoe-laurent"], ["Web Data", "AI Agents"],
     "Fresh, clean web data as agent fuel: schemas, dedupe, and "
     "change feeds."),
    ("t12", "Closing Panel: The Hallway Track", "17:00", "17:30",
     "Main Stage", ["maya-chen", "sam-okafor", "lena-fischer"],
     ["Open Source"],
     "The best conversations were not on the schedule. A panel about that."),
    ("t18", "Community Showcase: Lightning Demos", "17:30", "18:00",
     "Main Stage", ["sam-okafor", "diego-fuentes"],
     ["Open Source", "Developer Tools"],
     "Five minute demos from the floor: the projects people actually "
     "shipped this month."),
]

# person_a, person_b, note, at  (pre-existing memory: proves MET reads work
# and that Matchmaker will not re-suggest someone already met)
MEETINGS = [
    ("rene", "tom-alvarez",
     "Met at breakfast. Talked MCP gateways and code review bots.", "08:55"),
]


def connect(graph_name=None, url=None):
    url = url or os.environ.get("FALKORDB_URL", "redis://localhost:6379")
    name = graph_name or os.environ.get("HALLWAY_GRAPH", "hallway")
    db = FalkorDB.from_url(url)
    return db.select_graph(name)


def seed(g, fresh=True):
    """Create the sample conference in graph g. Returns a counts dict."""
    if fresh:
        try:
            g.delete()
        except Exception:
            pass

    for topic in TOPICS:
        g.query("MERGE (:Topic {name: $name})", {"name": topic})
    for room in ROOMS:
        g.query("MERGE (:Room {name: $name})", {"name": room})

    companies = sorted({p[3] for p in PEOPLE})
    for company in companies:
        g.query("MERGE (:Company {name: $name})", {"name": company})

    for pid, name, kind, company, handle in PEOPLE:
        g.query(
            "MERGE (p:Person {id: $id}) "
            "SET p.name = $name, p.kind = $kind, p.company = $company, "
            "p.handle = $handle",
            {"id": pid, "name": name, "kind": kind,
             "company": company, "handle": handle},
        )
        g.query(
            "MATCH (p:Person {id: $id}), (c:Company {name: $company}) "
            "MERGE (p)-[:WORKS_AT]->(c)",
            {"id": pid, "company": company},
        )

    for pid, topic, weight in INTERESTS:
        g.query(
            "MATCH (p:Person {id: $id}), (t:Topic {name: $topic}) "
            "MERGE (p)-[r:INTERESTED_IN]->(t) SET r.weight = $weight",
            {"id": pid, "topic": topic, "weight": weight},
        )

    for tid, title, starts, ends, room, speakers, topics, blurb in TALKS:
        g.query(
            "MERGE (t:Talk {id: $id}) SET t.title = $title, "
            "t.starts = $starts, t.ends = $ends, t.blurb = $blurb",
            {"id": tid, "title": title, "starts": starts,
             "ends": ends, "blurb": blurb},
        )
        g.query(
            "MATCH (t:Talk {id: $id}), (r:Room {name: $room}) "
            "MERGE (t)-[:IN_ROOM]->(r)",
            {"id": tid, "room": room},
        )
        for speaker in speakers:
            g.query(
                "MATCH (p:Person {id: $pid}), (t:Talk {id: $tid}) "
                "MERGE (p)-[:GIVES]->(t)",
                {"pid": speaker, "tid": tid},
            )
        for topic in topics:
            g.query(
                "MATCH (t:Talk {id: $id}), (tp:Topic {name: $topic}) "
                "MERGE (t)-[:ABOUT]->(tp)",
                {"id": tid, "topic": topic},
            )

    for a, b, note, at in MEETINGS:
        g.query(
            "MATCH (a:Person {id: $a}), (b:Person {id: $b}) "
            "MERGE (a)-[m:MET]->(b) SET m.note = $note, m.at = $at",
            {"a": a, "b": b, "note": note, "at": at},
        )

    return {"people": len(PEOPLE), "talks": len(TALKS),
            "topics": len(TOPICS), "meetings": len(MEETINGS)}


def main():
    g = connect()
    counts = seed(g)
    print(f"Seeded graph: {counts}")


if __name__ == "__main__":
    main()
