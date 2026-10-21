import { useState } from 'react';

export default function BuildProbe() {
  const [count, setCount] = useState(0);
  return (
    <section aria-label="Synthetic interaction check">
      <button type="button" onClick={() => setCount(value => value + 1)}>Increment synthetic counter</button>
      <p role="status" aria-live="polite">Synthetic count: {count}</p>
    </section>
  );
}
