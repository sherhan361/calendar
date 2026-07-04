import "@typespec/http";
import "@typespec/openapi";
import "@typespec/openapi3";

import "./models/common.tsp";
import "./models/users.tsp";
import "./models/schedules.tsp";
import "./models/event-types.tsp";
import "./models/share-links.tsp";
import "./models/slots.tsp";
import "./models/bookings.tsp";

import "./routes/auth.tsp";
import "./routes/me.tsp";
import "./routes/schedules.tsp";
import "./routes/event-types.tsp";
import "./routes/share-links.tsp";
import "./routes/slots.tsp";
import "./routes/bookings.tsp";

using Http;
using OpenAPI;

@service(#{ title: "Calendar API" })
@server("http://localhost:8000", "Local development server")
namespace Calendar;
