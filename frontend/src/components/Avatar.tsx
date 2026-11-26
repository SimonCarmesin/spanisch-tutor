/** Gesprächspartnerin mit Klangwellen. Die Wellen bewegen sich, während sie "spricht" (antwortet). */
export function Avatar({ name, speaking }: { name: string; speaking: boolean }) {
  const bars = [8, 16, 10, 22, 14, 28, 18, 12, 20, 9];
  const wave = (side: "left" | "right") => (
    <div className={`wave wave-${side} ${speaking ? "wave-active" : ""}`} aria-hidden="true">
      {(side === "left" ? bars : [...bars].reverse()).map((h, i) => (
        <span key={i} style={{ height: h, animationDelay: `${i * 70}ms` }} />
      ))}
    </div>
  );
  return (
    <div className="avatar-block">
      <div className="avatar-row">
        {wave("left")}
        <svg className="avatar" viewBox="0 0 120 120" role="img" aria-label={name}>
          <circle cx="60" cy="60" r="60" fill="#dbe7f6" />
          <path d="M28 108c4-20 18-30 32-30s28 10 32 30" fill="#fff" stroke="#9fbbe0" strokeWidth="2" />
          <path d="M34 62c0-22 11-36 26-36s26 14 26 36v20H34z" fill="#3b3f4a" />
          <ellipse cx="60" cy="60" rx="19" ry="22" fill="#f3d9c7" />
          <path d="M41 52c4-12 12-17 19-17s15 5 19 17c-7-4-13-9-19-10-6 1-12 6-19 10z" fill="#3b3f4a" />
          <circle cx="53" cy="60" r="1.8" fill="#3b3f4a" />
          <circle cx="67" cy="60" r="1.8" fill="#3b3f4a" />
          <path d="M54 70c3 3 9 3 12 0" stroke="#3b3f4a" strokeWidth="1.8" fill="none" strokeLinecap="round" />
          <path d="M36 60a24 24 0 0 1 48 0" stroke="#7fa8dc" strokeWidth="4" fill="none" />
          <rect x="31" y="56" width="8" height="14" rx="4" fill="#7fa8dc" />
          <rect x="81" y="56" width="8" height="14" rx="4" fill="#7fa8dc" />
        </svg>
        {wave("right")}
      </div>
      <p className="avatar-name">{name}</p>
    </div>
  );
}
