import { useState } from "react";
import type { FormEvent } from "react";
import { Form } from "@base-ui-components/react/form";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { t } from "../../lib/i18n";

type LoginScreenProps = {
  loading: boolean;
  error: string;
  onLogin: (email: string, password: string) => Promise<void>;
};

export function LoginScreen({ loading, error, onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo");

  async function submit(event: FormEvent) {
    event.preventDefault();
    await onLogin(email, password);
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="brand large">{t.brand}</div>
        <div>
          <p className="eyebrow">{t.login.eyebrow}</p>
          <h1>{t.login.title}</h1>
          <p className="muted">{t.login.hint}</p>
        </div>
        {error ? <div className="banner error">{error}</div> : null}
        <Form className="stack" onSubmit={submit}>
          <TextField label={t.login.email} type="email" value={email} onChange={setEmail} />
          <TextField label={t.login.password} type="password" value={password} onChange={setPassword} />
          <Button variant="primary" type="submit" disabled={loading}>
            {loading ? t.login.submitting : t.login.submit}
          </Button>
        </Form>
      </section>
    </main>
  );
}
