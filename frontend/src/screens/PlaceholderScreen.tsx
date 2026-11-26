export function PlaceholderScreen({ title, text }: { title: string; text: string }) {
  return (
    <section className="screen placeholder">
      <h1>{title}</h1>
      <p className="muted">{text}</p>
    </section>
  );
}
