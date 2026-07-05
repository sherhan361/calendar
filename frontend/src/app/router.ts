import { useEffect, useState } from "react";

export type AppRoute =
  | { kind: "app" }
  | {
      kind: "public-booking";
      username: string;
      slug: string;
      shareToken?: string;
    }
  | {
      kind: "public-cancel";
      uid: string;
      token: string;
    };

export function parseRoute(): AppRoute {
  const hash = window.location.hash || "#";
  const [path, query = ""] = hash.slice(1).split("?");
  const parts = path.split("/").filter(Boolean);
  const params = new URLSearchParams(query);
  if (parts[0] === "book" && parts[1] && parts[2]) {
    return {
      kind: "public-booking",
      username: parts[1],
      slug: parts[2],
      shareToken: params.get("shareToken") ?? undefined,
    };
  }
  if (parts[0] === "cancel" && parts[1]) {
    return {
      kind: "public-cancel",
      uid: parts[1],
      token: params.get("token") ?? "",
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
