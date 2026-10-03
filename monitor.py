#!/usr/bin/env python3
"""
Research Monitor Bot — Gordon Pipa
Monitors arXiv, Google Scholar, and blogs for papers related to:
- Self-organizing recurrent spiking networks (SORN)
- Transfer entropy & effective connectivity
- Neural synchrony & oscillations
- Cross-frequency coupling
- Information processing in recurrent networks
"""

import json
import subprocess
import re
import sys
import os
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent
DB_PATH = WORKSPACE / "research_db.json"
OUTPUT_DIR = WORKSPACE / "outputs"
LOG_PATH = WORKSPACE / "monitor.log"

# ─── Key concept pairs to search ───
SEARCH_TEMPLATES = [
    # Core SORN / self-organizing spiking networks
    ["self-organizing recurrent spiking neural network", ["self-organization", "plasticity", "homeostasis", "criticality"]],
    ["spiking neural network self-organizing", ["spiking", "recurrent", "self-organization"]],
    ["recurrent network self-organizing dynamics", ["recurrent", "self-organizing", "attractor"]],
    ["spiking network homeostatic plasticity", ["spiking", "homeostasis", "plasticity", "criticality"]],
    ["neuronal avalanche self-organized criticality", ["criticality", "avalanche", "scale-free"]],
    # Information processing via transfer entropy / effective connectivity
    ["transfer entropy neural network information flow", ["transfer entropy", "effective connectivity", "information flow"]],
    ["effective connectivity neural computation", ["effective connectivity", "information flow", "causality"]],
    ["information theoretic measure neural synchrony", ["information theory", "synchrony", "mutual information"]],
    ["recurrent network information processing principles", ["recurrent", "information processing", "temporal"]],
    # Oscillations, synchrony, cross-frequency
    ["neural synchrony oscillation dynamics", ["synchrony", "oscillations", "gamma", "rhythm"]],
    ["cross-frequency coupling neural oscillations", ["cross-frequency", "coupling", "multi-scale"]],
    ["gamma oscillations recurrent network", ["gamma", "oscillation", "recurrent"]],
    # Temporal processing, memory, predictive coding
    ["recurrent network fading memory temporal", ["fading memory", "temporal", "recurrent", "prediction"]],
    ["predictive coding spiking neural network", ["predictive coding", "spiking", "prediction", "error"]],
    ["temporal dynamics attractor neural network", ["attractor", "temporal", "dynamics", "recurrent"]],
    # Spiking network learning & STDP
    ["spike timing dependent plasticity recurrent", ["STDP", "plasticity", "spiking", "recurrent"]],
    ["credit assignment spiking neural network", ["credit assignment", "spiking", "learning", "STDP"]],
    ["biologically plausible learning spiking network", ["plausible", "spiking", "learning", "biology"]],
    # Network structure & topology
    ["network topology extract neural recording", ["topology", "network", "extraction", "recording"]],
    ["connectome constrained neural dynamics", ["connectome", "network", "dynamics"]],
    # Criticality & phase transitions in neural systems
    ["criticality neural system phase transition", ["criticality", "phase transition", "neural"]],
    ["neural system self-organized criticality", ["self-organized criticality", "neural", "avalanche"]],
    # Reservoir computing & neuromorphic
    ["reservoir computing spiking recurrent", ["reservoir", "spiking", "recurrent", "neuromorphic"]],
    ["neuromorphic computing recurrent dynamics", ["neuromorphic", "recurrent", "dynamics"]],
    # State space dynamics
    ["state space dynamics neural computation", ["state space", "dynamics", "computation"]],
    ["high-dimensional neural dynamics", ["high-dimensional", "dynamics", "neural"]],
]

YOUR_RESEARCH_TOPICS = {
    "SORN": ["self-organizing recurrent", "plasticity homeostasis", "stable learning"],
    "Transfer Entropy": ["effective connectivity", "information flow", "causal inference"],
    "Neural Synchrony": ["synchrony", "gamma", "oscillation", "rhythm"],
    "Cross-Frequency": ["cross-frequency", "multi-scale", "coupling"],
    "Fading Memory": ["memory", "temporal", "recurrent prediction"],
    "Network Topology": ["topology", "network extraction", "structure"],
    "Dynamical Relaying": ["relaying", "delay", "synchrony"],
    "Criticality": ["criticality", "avalanche", "scale-free"],
}


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.write_bytes((line + "\n").encode("utf-8")) if not LOG_PATH.exists() else LOG_PATH.write_text(line + "\n", encoding="utf-8")


def fetch_arxiv_papers():
    """Fetch recent arXiv papers in relevant categories."""
    papers = []
    categories = ["q-bio.NC", "cs.NE", "cs.LG", "q-bio.QM"]

    for cat in categories:
        try:
            url = f"https://arxiv.org/list/{cat}/recent"
            out = subprocess.run(
                f'curl -s "{url}" --connect-timeout 15',
                shell=True, capture_output=True, text=True, timeout=20
            )
            if out.returncode == 0 and len(out.stdout) > 500:
                # Extract paper IDs
                ids = re.findall(r'arXiv:(\d+\.\d+(?:v\d+)?)', out.stdout)
                ids = list(dict.fromkeys(ids))[:10]  # Deduplicate, take first 10

                for pid in ids:
                    try:
                        abs_url = f"https://arxiv.org/abs/{pid}"
                        out2 = subprocess.run(
                            f'curl -s "{abs_url}" --connect-timeout 10',
                            shell=True, capture_output=True, text=True, timeout=15
                        )
                        if len(out2.stdout) > 1000:
                            # Extract title
                            title_m = re.search(
                                r'<h1[^>]*class="title mathjax"[^>]*>(.*?)</h1>',
                                out2.stdout, re.DOTALL
                            )
                            if title_m:
                                title = re.sub(r'<[^>]+>', '', title_m.group(1))
                                title = re.sub(r'\s+', ' ', title).strip()
                                title = title.split('$')[0].strip()
                                # Strip common prefixes from arXiv HTML structure
                                for prefix in ['Title:', 'Title :']:
                                    if title.startswith(prefix):
                                        title = title[len(prefix):].strip()
                                # Remove any remaining mathjax artifacts
                                title = re.sub(r'\\[.*?\\]', '', title)  # Remove LaTeX blocks
                                title = re.sub(r'\$.*?\$', '', title)  # Remove inline math
                                title = re.sub(r'\s+', ' ', title).strip()

                            # Extract abstract
                            abs_m = re.search(
                                r'<blockquote[^>]*class="abstract mathjax"[^>]*>(.*?)</blockquote>',
                                out2.stdout, re.DOTALL
                            )
                            abstract = ""
                            if abs_m:
                                abstract = re.sub(r'<[^>]+>', ' ', abs_m.group(1))
                                abstract = re.sub(r'\s+', ' ', abstract).strip()
                                abstract = abstract.split('$')[0].strip()

                            # Extract authors
                            authors_m = re.findall(
                                r'<a[^>]*class="author"[^>]*>(.*?)</a>',
                                out2.stdout, re.DOTALL
                            )
                            authors = []
                            for a in authors_m:
                                author = re.sub(r'<[^>]+>', '', a)
                                author = re.sub(r'\s+', ' ', author).strip()
                                authors.append(author)

                            # Extract categories
                            cats = []
                            for cm in re.finditer(r'name="dc\.subject"[^>]*content="(.*?)"', out2.stdout):
                                cats.extend(cm.group(1).split('; '))
                            if not cats:
                                cat_m = re.search(r'arxiv.*?category.*?value="(.*?)"', out2.stdout, re.I)
                                if cat_m:
                                    cats = [cat_m.group(1)]

                            papers.append({
                                "id": pid,
                                "title": title,
                                "abstract": abstract[:2000],
                                "authors": authors[:10],
                                "categories": cats,
                                "url": abs_url,
                                "source": f"arXiv:{cat}",
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "keywords": extract_keywords(title, abstract)
                            })
                    except Exception as e:
                        log(f"Error fetching {pid}: {e}")

        except Exception as e:
            log(f"Error fetching {cat}: {e}")

    return papers


def extract_keywords(title, abstract):
    """Extract relevant keywords from title/abstract."""
    text = (title + " " + abstract).lower()
    keywords = []
    key_terms = [
        "spiking", "recurrent", "plasticity", "homeostasis", "criticality",
        "transfer entropy", "synchrony", "oscillation", "attractor",
        "self-organizing", "information flow", "effective connectivity",
        "cross-frequency", "fading memory", "predictive coding", "STDP",
        "reservoir computing", "neuromorphic", "avalanche", "state space",
        "connectome", "brain", "neural", "network", "dynamics", "learning",
        "temporal", "memory", "coding", "oscillation", "gamma", "rhythm",
        "phase transition", "scale-free", "topology", "dynamical relaying"
    ]
    for term in key_terms:
        if term.lower() in text:
            keywords.append(term)
    return keywords


def match_to_your_research(paper):
    """Score how relevant a paper is to Gordon Pipa's research."""
    title = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()

    scores = {}
    for topic, terms in YOUR_RESEARCH_TOPICS.items():
        score = sum(1 for t in terms if t in title)
        if score > 0:
            scores[topic] = score

    # Also check keywords
    keyword_matches = [k for k in paper.get("keywords", []) if k in
                       ["spiking", "recurrent", "self-organization", "criticality",
                        "transfer entropy", "effective connectivity", "synchrony",
                        "oscillation", "cross-frequency", "fading memory",
                        "attractor", "plasticity", "reservoir computing",
                        "neuromorphic", "state space", "connectome"]]

    total_score = sum(scores.values()) + len(keyword_matches)

    return {
        "relevance_score": total_score,
        "matching_topics": scores,
        "keyword_matches": keyword_matches
    }


def analyze_paper(paper):
    """Analyze what's novel and how it connects to the user's work."""
    title = paper.get("title", "").replace("Title:", "").strip()
    abstract = paper.get("abstract", "").replace("Abstract:", "").strip()
    relevance = match_to_your_research(paper)

    # Generate analysis
    analysis = {
        "id": paper.get("id", ""),
        "title": title,
        "abstract": abstract[:2000],
        "authors": paper.get("authors", []),
        "source": paper.get("source", ""),
        "url": paper.get("url", ""),
        "relevance": relevance,
        "novelty": detect_novelty(title, abstract),
        "connection_to_your_work": find_connections(title, abstract, relevance),
        "potential_benefit": suggest_benefits(title, abstract, relevance),
        "key_insights": extract_key_insights(title, abstract),
    }
    return analysis


def detect_novelty(title, abstract):
    """Detect what's novel in the paper."""
    novelty_signals = []

    if any(w in abstract.lower() for w in ["novel", "new", "first", "前所未有", "首次"]):
        novelty_signals.append("Claims novelty")

    if "proposed" in abstract.lower():
        novelty_signals.append("Proposes new method/approach")

    if "demonstrate" in abstract.lower() or "show" in abstract.lower():
        novelty_signals.append("Provides experimental/empirical evidence")

    if "extend" in abstract.lower() or "generalize" in abstract.lower():
        novelty_signals.append("Extends existing framework")

    if "challenge" in abstract.lower() or "debate" in abstract.lower():
        novelty_signals.append("Challenges existing assumptions")

    if any(term in abstract.lower() for term in ["criticality", "self-organized criticality", "neuronal avalanche"]):
        novelty_signals.append("Addresses criticality/avalanche phenomena")

    if any(term in abstract.lower() for term in ["spiking neural network", "spiking", "SNN"]):
        novelty_signals.append("Works with spiking neural networks")

    if any(term in abstract.lower() for term in ["recurrent", "recurrent neural network", "RNN"]):
        novelty_signals.append("Focuses on recurrent network architecture")

    if any(term in abstract.lower() for term in ["plasticity", "homeostasis", "synaptic", "STDP"]):
        novelty_signals.append("Examines plasticity/homeostasis mechanisms")

    if any(term in abstract.lower() for term in ["information flow", "effective connectivity", "transfer entropy"]):
        novelty_signals.append("Studies information flow/connectivity")

    if any(term in abstract.lower() for term in ["synchrony", "oscillation", "gamma", "rhythm", "phase lock"]):
        novelty_signals.append("Investigates synchrony/oscillations")

    if not novelty_signals:
        novelty_signals.append("General theoretical or empirical work")

    return novelty_signals


def find_connections(title, abstract, relevance):
    """Find connections to Gordon Pipa's research."""
    connections = []

    title_lower = (title + " " + abstract).lower()

    if "self-organizing" in title_lower or "plasticity" in title_lower or "homeostasis" in title_lower:
        connections.append("Directly relates to SORN (self-organizing recurrent network) framework")

    if "transfer entropy" in title_lower or "effective connectivity" in title_lower or "causal" in title_lower:
        connections.append("Relates to transfer entropy framework for measuring information flow")

    if "synchrony" in title_lower or "oscillation" in title_lower or "gamma" in title_lower:
        connections.append("Related to neural synchrony and gamma oscillation research")

    if "cross-frequency" in title_lower:
        connections.append("Relates to cross-frequency coupling in neuroscience")

    if "memory" in title_lower or "temporal" in title_lower or "delay" in title_lower:
        connections.append("Relevant to fading memory and temporal processing work")

    if "topology" in title_lower or "network structure" in title_lower:
        connections.append("Relates to network topology extraction work")

    if "relaying" in title_lower or "conduction delay" in title_lower:
        connections.append("Connects to dynamical relaying research")

    if "criticality" in title_lower or "avalanche" in title_lower:
        connections.append("Related to criticality in neural systems")

    if "recurrent" in title_lower and "information" in title_lower:
        connections.append("Addresses information processing in recurrent networks")

    if "predictive" in title_lower or "prediction" in title_lower:
        connections.append("Relates to predictive coding and temporal prediction")

    if not connections:
        connections.append("Indirectly related — explore for cross-disciplinary insights")

    return connections


def suggest_benefits(title, abstract, relevance):
    """Suggest how this paper could benefit the user's research."""
    benefits = []

    title_lower = (title + " " + abstract).lower()

    if any(t in title_lower for t in ["model", "framework", "theoretical", "principle"]):
        benefits.append("May provide new theoretical insights applicable to your frameworks")

    if "criticality" in title_lower or "avalanche" in title_lower:
        benefits.append("May inform your work on self-organized criticality in networks")

    if "spiking" in title_lower and "plasticity" in title_lower:
        benefits.append("Could extend your understanding of self-organizing plasticity in spiking networks")

    if "information" in title_lower and ("flow" in title_lower or "transfer" in title_lower):
        benefits.append("May offer new perspectives on information flow measurement")

    if "oscillation" in title_lower or "synchrony" in title_lower:
        benefits.append("Could provide new mechanisms for oscillation generation in recurrent networks")

    if "learning" in title_lower and "biological" in title_lower:
        benefits.append("May inspire biologically plausible learning rules for your networks")

    if "dynamics" in title_lower and ("attractor" in title_lower or "state" in title_lower):
        benefits.append("Could reveal new dynamical principles in recurrent networks")

    if "temporal" in title_lower or "memory" in title_lower:
        benefits.append("May extend your fading memory analysis to new regimes")

    if "reservoir" in title_lower:
        benefits.append("Could relate to your recurrent network dynamics work")

    if not benefits:
        benefits.append("Explore for potential cross-disciplinary applications")

    return benefits[:3]  # Keep top 3


def extract_key_insights(title, abstract):
    """Extract key insights from the paper."""
    insights = []

    # Look for numbered insights or key findings
    text = abstract[:3000]  # Analyze first 3000 chars

    if "result" in text.lower():
        insights.append("Presents experimental/computational results")

    if "show" in text.lower() or "demonstrate" in text.lower():
        insights.append("Demonstrates specific phenomena or capabilities")

    if "suggest" in text.lower() or "indicate" in text.lower():
        insights.append("Suggests new theoretical directions")

    if "method" in text.lower() or "approach" in text.lower():
        insights.append("Introduces new methodological approach")

    if "implication" in text.lower() or "implication" in text.lower():
        insights.append("Discusses broader implications")

    if any(term in text.lower() for term in ["recurrent", "spiking", "network", "dynamic"]):
        insights.append("Focuses on network-level dynamics")

    if any(term in text.lower() for term in ["brain", "neural", "cortical", "cortex"]):
        insights.append("Has biological/neural implications")

    if not insights:
        insights.append("Theoretical or computational analysis")

    return insights


def generate_report(analysis_list, date=None):
    """Generate a formatted report from analyzed papers."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    report_path = OUTPUT_DIR / f"report_{date}.md"

    # Sort by relevance
    analysis_list.sort(key=lambda x: x["relevance"]["relevance_score"], reverse=True)

    report = f"""# Research Monitor Report — {date}

## Summary

**Date:** {date}
**Papers Analyzed:** {len(analysis_list)}
**Highly Relevant (score >= 3):** {sum(1 for a in analysis_list if a['relevance']['relevance_score'] >= 3)}
**Moderately Relevant (score 1-2):** {sum(1 for a in analysis_list if 1 <= a['relevance']['relevance_score'] < 3)}
**Weakly Relevant (score 0):** {sum(1 for a in analysis_list if a['relevance']['relevance_score'] == 0)}

---

## Top Papers — Direct Connection to Your Research

"""

    # Top 5 most relevant papers
    top_papers = [a for a in analysis_list if a['relevance']['relevance_score'] >= 2][:5]

    for i, paper in enumerate(top_papers, 1):
        report += f"""### {i}. {paper['title']}

**Source:** {paper['relevance']['keyword_matches']}
**Matching Topics:** {dict(paper['relevance']['matching_topics'])}

**What's New:**
"""
        for n in paper['novelty']:
            report += f"- {n}\n"

        report += """
**Why This Matters to You:**
"""
        for c in paper['connection_to_your_work']:
            report += f"- {c}\n"

        report += "\n**How You Can Benefit:**\n"
        for b in paper['potential_benefit']:
            report += f"- {b}\n"

        report += "\n"

    # All other papers
    if len(analysis_list) > len(top_papers):
        report += "\n---\n\n## All Papers Found\n\n"
        for paper in analysis_list[len(top_papers):]:
            report += f"- {paper['title']} (arXiv:{paper['id']}) — Relevance: {paper['relevance']['relevance_score']}\n"

    report += f"\n\n---\n\n## Mindmap\n\nOpen `mindmap.html` in your browser to see the interactive mindmap visualization of your research positioned against new findings.\n"

    report_path.write_text(report, encoding="utf-8")
    return report_path


def main():
    """Main monitoring loop."""
    log("Starting research monitoring run")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch papers from arXiv
    papers = fetch_arxiv_papers()
    log(f"Fetched {len(papers)} papers from arXiv")

    if not papers:
        log("No papers fetched — exiting")
        return

    # Analyze each paper
    analyses = []
    for paper in papers:
        analysis = analyze_paper(paper)
        analyses.append(analysis)
        log(f"Analyzed: {paper['title'][:60]}... (relevance: {analysis['relevance']['relevance_score']})")

    # Generate report
    report_path = generate_report(analyses)
    log(f"Report generated: {report_path}")

    # Save full analysis data
    data_path = OUTPUT_DIR / "analyses.json"
    with open(data_path, 'w') as f:
        json.dump(analyses, f, indent=2, default=str)
    log(f"Full data saved: {data_path}")

    log("Research monitoring run complete")


if __name__ == "__main__":
    main()
