# Separate Domain Rules From API Adapters

The backend exposes HTTP contracts, but slot generation, booking creation, and booking status transitions are calendar-domain rules rather than route-handler details. We decided to keep FastAPI routes as adapters, put transaction orchestration in application use cases, and keep availability and status rules in a domain module so slot listing and booking creation evaluate the same rules.

**Considered Options**

- Keep the rules directly in FastAPI routes.
- Move the rules into ORM models.
- Use a separate domain module plus application use cases.

**Consequences**

- Calendar rules can be tested without HTTP or database setup.
- Routes stay thin, but application use cases still own persistence orchestration.
- The domain layer must not import API, ORM, or frontend contract types.
