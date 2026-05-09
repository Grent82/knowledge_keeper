export function App() {
  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">Knowledge Keeper</p>
        <h1>Private media and knowledge platform</h1>
        <p className="intro">
          Local-first foundation for a private audio, video and markdown-based knowledge system.
        </p>
      </section>

      <section className="grid">
        <article className="card">
          <h2>Media library</h2>
          <p>Upload local media, register external sources and organize everything by category.</p>
        </article>
        <article className="card">
          <h2>Playback progress</h2>
          <p>Persist audio and video progress per user without leaking activity between accounts.</p>
        </article>
        <article className="card">
          <h2>Knowledge notes</h2>
          <p>Prepare markdown-first notes, summaries and semantic links in later phases.</p>
        </article>
      </section>
    </main>
  );
}
