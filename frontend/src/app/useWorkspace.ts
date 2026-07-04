import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { asErrorMessage } from "../lib/utils";
import type { Booking, EventType, Schedule, User } from "../lib/types";

const TOKEN_KEY = "calendar:token";

export type Workspace = {
  token: string;
  user: User | null;
  eventTypes: EventType[];
  schedules: Schedule[];
  bookings: Booking[];
  loading: boolean;
  error: string;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
};

export function useWorkspace(): Workspace {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) ?? "");
  const [user, setUser] = useState<User | null>(null);
  const [eventTypes, setEventTypes] = useState<EventType[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refreshWorkspace = useCallback(async (activeToken: string) => {
    setLoading(true);
    setError("");
    try {
      const [nextUser, nextSchedules, nextEventTypes, nextBookings] = await Promise.all([
        api.me(activeToken),
        api.listSchedules(activeToken),
        api.listEventTypes(activeToken),
        api.listBookings(activeToken),
      ]);
      setUser(nextUser);
      setSchedules(nextSchedules.items);
      setEventTypes(nextEventTypes.items);
      setBookings(nextBookings.items);
    } catch (requestError) {
      setError(asErrorMessage(requestError));
      localStorage.removeItem(TOKEN_KEY);
      setToken("");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!token) return;
    void refreshWorkspace(token);
  }, [token, refreshWorkspace]);

  const login = useCallback(
    async (email: string, password: string) => {
      setLoading(true);
      setError("");
      try {
        const session = await api.login(email, password);
        localStorage.setItem(TOKEN_KEY, session.accessToken);
        setToken(session.accessToken);
        setUser(session.user);
        await refreshWorkspace(session.accessToken);
      } catch (requestError) {
        setError(asErrorMessage(requestError));
      } finally {
        setLoading(false);
      }
    },
    [refreshWorkspace],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setUser(null);
    setEventTypes([]);
    setSchedules([]);
    setBookings([]);
  }, []);

  const refresh = useCallback(async () => {
    if (token) await refreshWorkspace(token);
  }, [token, refreshWorkspace]);

  return { token, user, eventTypes, schedules, bookings, loading, error, login, logout, refresh };
}
