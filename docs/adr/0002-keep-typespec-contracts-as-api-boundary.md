# Keep TypeSpec Contracts As The API Boundary

The frontend and backend share a TypeSpec contract that predates the FastAPI backend. We decided to preserve TypeSpec as the external API boundary and map FastAPI request and response models into application use cases, rather than deriving the domain model from transport shapes.

**Considered Options**

- Generate backend models directly from TypeSpec/OpenAPI.
- Treat Pydantic request and response models as domain entities.
- Keep contract DTOs at the API edge and map into application/domain code.

**Consequences**

- Contract compatibility remains explicit.
- The backend carries some mapping code.
- Domain language can use terms like Host and Slot even when the API still exposes compatibility names such as owner or user.
