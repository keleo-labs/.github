# Keleo

**An open, composable framework for describing working practices and methods — across any domain.**

## Open Source Methods and Practice

The hyperscalers have largely converged on the concept of a [Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/) (WAF). AWS, Azure, and Google each publish one, and the overlap is striking — they agree on pillars like security, reliability, performance, cost optimisation, and operational excellence. Companion [Cloud Adoption Frameworks](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/) (CAFs) address the organisational journey to cloud: strategy, governance, people, and process.

These are useful, but they share a fundamental limitation: **each is proprietary, vendor-coupled, and monolithic**. The guidance assumes the vendor's own services. The review tools only work inside the vendor's console. There is no shared schema, no interoperability, and no way for a community to extend or compose practices across them. Organisations operating in multi-cloud or hybrid environments maintain parallel, largely redundant review processes with incompatible outputs.

This pattern — good ideas locked inside monolithic, top-down frameworks — isn't unique to cloud. It's how the industry treats methodology in general. We favour monoliths when we describe how to work, even though we've long since abandoned them in how we build software.

## Modular Practices

We solved this problem for infrastructure. **Kubernetes and the CNCF landscape** demonstrate what a composable, competitive ecosystem looks like in practice. Rather than adopting a single vendor's monolithic platform, organisations assemble purpose-built stacks from interoperable, best-of-breed tools — Kubernetes for orchestration, Prometheus for metrics, Envoy for service proxy — all connected through open standards. Multiple competing projects exist in each category, driving innovation through competition rather than vendor fiat.

Why can't we do the same for practices and methodology?

No one wants a one-size-fits-all solution. The common challenge is competing approaches, but competition is a feature, not a bug — as long as the underlying structure lets you compose and compare. What's missing is the shared language and kernel that makes practices interoperable.

## The Approach

Keleo draws on [SEMAT Essence](https://www.omg.org/spec/Essence/) — a standard created by Ivar Jacobson, Bertrand Meyer, and Richard Soley to put software engineering methods on a more rigorous footing. Essence separates the universal *what* (a kernel of things that are always present in any endeavour) from the variable *how* (practices that teams choose and compose). Practices become modular, comparable, and composable — a team assembles its method from independent practices rather than adopting a monolithic methodology wholesale.

Keleo modernises these ideas and generalises them beyond software engineering. The framework has four layers:

| Layer | Purpose | Analogy |
|---|---|---|
| **Language** | A schema for expressing practices and guidance — how you organise your thoughts around things to be concerned about (alphas, states) and things to do (activities, work products). | The grammar |
| **Baseline** | A practice kernel providing the common essential elements you see in all practices for a given domain. | The common ground — like the five pillars that AWS and Azure agree on in their respective WAFs |
| **Practices** | Extend and specialise aspects of the baseline with specific guidance, patterns, and approaches. | The competing ecosystem — multiple ways to address the same concern |
| **Methods** | Compose practices together into a combined, cohesive method. | The assembled stack — your team's chosen way of working |

Everything is written in JSON, and software merges content together into a cohesive view — whether you're interested in a single practice or a complete method.

## Repositories

| Repository | Description |
|---|---|
| [keleo-language](https://github.com/keleo-labs/keleo-language) | The Practice Language JSON Schema — the meta-model for describing practices, methods, and baselines. Defines the structural hierarchy of alphas, states, work products, activities, personas, and patterns. |
| [keleo-studio](https://github.com/keleo-labs/keleo-studio) | A practice management and method composition application. Validates, visualises, and merges practice content into cohesive views. |
| [keleo-pgen-llm](https://github.com/keleo-labs/keleo-pgen-llm) | An LLM-powered pipeline that converts methodology documentation into schema-compliant Practice Language JSON. |
| [keleo-platforms](https://github.com/keleo-labs/keleo-platforms) | Practices and methods for infrastructure platform engineering — the primary domain this framework was built for. |
| [keleo-template](https://github.com/keleo-labs/keleo-template) | A template repository for creating your own practice and method content. |
| [keleo-horticulture](https://github.com/keleo-labs/keleo-horticulture) | A demonstration that the framework works beyond IT — professional horticulture modelled as structured, composable practices. |
| [keleo-horticulture-docs](https://github.com/keleo-labs/keleo-horticulture-docs) | Source documentation for the horticulture domain, used as input to the generation pipeline. |

## Wait, Horticulture!?

The horticulture example exists to prove a point: if a framework for describing practices only works for software engineering, it isn't really a framework for describing practices — it's just another methodology. Modelling biological systems, production operations, and professional governance alongside platform engineering demonstrates that the language and kernel are genuinely domain-agnostic.

## Status

This is a working prototype. The language schema is stable, the studio application is functional, and there are real practice sets for both platform engineering and horticulture. Contributions, feedback, and new domains are welcome.

## Getting Started

1. Browse [keleo-language](https://github.com/keleo-labs/keleo-language) to understand the Practice Language schema
2. Use [keleo-template](https://github.com/keleo-labs/keleo-template) a template repo for creating collaboration around new baselines and practices
3. Bootstrap your practice creation with [keleo-pgen-llm](https://github.com/keleo-labs/keleo-pgen-llm) - a set of Claude skills that help you create new baselines, practices and methods. Once you have the JSON created, you can use `keleo-studio` to improve and develop your practices. 
4. Use [keleo-studio](https://github.com/keleo-labs/keleo-studio) to validate, visualise, edit and compose practices into methods
5. See [keleo-platforms](https://github.com/keleo-labs/keleo-platforms) or [keleo-horticulture](https://github.com/keleo-labs/keleo-horticulture) for real-world examples

## Licence

See individual repositories for licence details.
