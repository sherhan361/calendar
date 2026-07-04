import { useEffect, useState } from "react";

export type AppRoute =
  | { kind: "app" }
  | {
      kind: "public-booking";
      username: string;
      slug: string;
      shareToken?: string;
    };

export function parseRoute(): AppRoute {
  const hash = window.location.hash || "#";
  const [path, query = ""] = hash.slice(1).split("?");
  const parts = path.split("/").filter(Boolean);
  if (parts[0] === "book" && parts[1] && parts[2]) {
    return {
      kind: "public-booking",
      username: parts[1],
      slug: parts[2],
      shareToken: new URLSearchParams(query).get("shareToken") ?? undefined,
    };
  }
  return { kind: "app" };
}

export function useHashRoute(): AppRoute {
  const [route, setRoute] = useState<AppRoute>(() => parseRoute());
  useEffect(() => {
    const onHashChange = () => setRoute(parseRoute());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);
  return route;
}
