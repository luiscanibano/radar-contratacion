import { Brand } from "@/components/Brand";
import { Button } from "@/components/ui/button";

export function AppTopBar({ email, onSalir }: { email?: string; onSalir?: () => void }) {
  return (
    <header className="flex items-center justify-between border-b border-border py-5">
      <Brand compact />
      <div className="flex items-center gap-3">
        {email && (
          <div className="flex items-center gap-3">
            <span className="hidden font-mono text-xs text-muted-foreground sm:inline">{email}</span>
            <Button type="button" variant="outline" size="sm" onClick={onSalir} className="rounded-full">
              Salir
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}
