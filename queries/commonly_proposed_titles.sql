--select  entity_id, annotation_key, annotation_value, reason
select  annotation_value, count(*)
from derived.prompt_response_annotations_string 
where 1=1
and annotation_key = 'proposed_title'
group by annotation_value
--having count(*) > 5
ORDER BY count(*) desc
;
--and source_version = '1.1';

/*
looks like we've got a bunch of records here where section
headers were tagged as title proposals.

    Definition
    Overview
    Key Concepts
    Formal Definition
    Core Concepts
    Background
    Mathematical Formulation
    Fundamental Concepts
    Historical Context
    Mathematical Definition
    Mathematical Framework
    Formal Statement
    Basic Concepts
    Roadmap
    Core Mechanisms & Doctrines
    Mathematical Formalism
    Key Components
    Mathematical Formalization
    General Setup
    Key Characteristics
    Mathematical Foundation
    Mathematical Foundations
    Theoretical Framework
    Introduction
    Theoretical Foundations
    Theoretical Foundation
    Formal Characterization
    Definition and Theoretical Framework
    Definition and Basic Properties
    Core Principles
    Formal Framework
    High-Level Intuition
    Requirements
    Formal Setting
    Core Definition


    Statement Of ...
    Overview Of ...
    1. ...
    Chapter 1. ...
    Deliverable 1. ...
    Phase 1. ....
    X and Y
    X as Y
    🧭 Roadmap
    🌐 Core Mechanisms & Doctrines
    📜 Setup
    📜 Definition
    📘 *Topos of Bricks: A Contextual Epistemology of Measurement*
    🧑‍💼 Political Actors (Individuals)
    🔄 Central Duality: States and Observables
    🏛️ Postal Accountability and Enhancement Act|PAEA of 2006
    🔴 Tier 1: High-Priority Core Concepts
    🧩 Nominal Compatibilism (Coherence)
    🎲 Hierarchical Probability and Epistemic Descriptions
    🥛 Smoothies, Milk, and Signal Detection Theory
    🧱 Sorting LEGO Bricks and Resolving Singularities: An Epistemic Analogy
    📘 Monograph Title (Working)
    💣 Commons Sabotage Pattern
    1️⃣ "Reason About"
    📏 Shattering Dimension and Epistemic Descriptions
    🧭 “I Am Whatever You Say I Am” vs. “I Am Who I Choose to Become”
    🧠 Formalization: No Global Section, No Natural Alignment
    📚 Probability Foundations: Kolmogorov Axioms, Events, and Observation
    🎲 Rademacher Complexity and Descriptive Events
    🧭 High-Level Intuition
    ✅ Phase 1: Full Articles for Brief Mentions / Partial Treatments
    🧮 Formal Setting: Model Theory
    🛠 Requirements
    🔹 Bahdanau Attention
    🧱 LEGO Distributions and LDA
    🎯 Classical Observables vs Quantum Observables
    🔍 Overview of MoSCoW
    📚 Updated Bibliography
    ⚙️ Mathematical Structure
    
*/