# Spanish pages — integration notes

Three new files, to be dropped in the repository root alongside the English originals:

- `index.es.html`
- `guide.es.html`
- `consortiumGuide.es.html`

They use the `.es.html` sibling naming rather than an `/es/` subdirectory so that every
relative link to an untranslated page (`completeness.html`, `rorRetriever.html`,
`useCases.html`, …) keeps working without a `../` prefix.

## What changed and what didn't

- All CSS and JavaScript is byte-for-byte identical to the English originals. Verified.
- All element IDs, class names, `onclick` handlers, and the `rcw-ga` localStorage key are
  unchanged, so analytics consent stays shared across the whole suite in both languages.
- `<html lang="en">` became `<html lang="es">` on each page.
- `hreflang` alternates were added to each page's `<head>`.

## Cross-linking

Links among these three pages point at the Spanish versions. Links to pages that have not
been translated still point at the English files and are marked `(EN)` in navigation lists.
Each page has an `English ↗` link at the top of the nav.

To complete the pairing, add a Spanish link to the three English pages. In `index.html`,
inside `<div class="topbar-links">`:

```html
<a href="index.es.html">Español ↗</a>
```

In `guide.html` and `consortiumGuide.html`, inside the first `<div class="topbar-col">`:

```html
<a href="guide.html">English ↗</a>          <!-- guide.html gets: -->
<a href="guide.es.html">Español ↗</a>
<a href="consortiumGuide.es.html">Español ↗</a>   <!-- consortiumGuide.html gets this -->
```

And the matching `hreflang` block in each English `<head>`, e.g. for `index.html`:

```html
<link rel="alternate" hreflang="en" href="index.html" />
<link rel="alternate" hreflang="es" href="index.es.html" />
<link rel="alternate" hreflang="x-default" href="index.html" />
```

## Translation choices worth reviewing

Register is *usted* throughout — the standard for professional documentation and neutral
across Spain and Latin America.

Key terms:

| English | Spanish used |
|---|---|
| metadata | metadatos |
| completeness | completitud |
| connectivity | conectividad |
| curation / re-curation | curación / recuración |
| use case | caso de uso |
| occurrence | aparición |
| entity | entidad |
| quick win | logro rápido |
| record | registro |
| creator / contributor | creador / contribuyente |
| funder / publisher | financiador / editor |
| bright spots | puntos brillantes |
| positive deviance | desviación positiva |
| Direct the Rider / Motivate the Elephant / Shape the Path | Dirigir al Jinete / Motivar al Elefante / Allanar el Camino |

Left in English on purpose:

- **Tool names** (Metadata Completeness, Re-Curation Watch, ROR Retriever, …) and **UI
  labels** quoted in the guides (`Explore`, `Max`, `Random sample`, `Find RORs`,
  `To fix`, `Potential duplicates`, `FAIR Total`, `Text`/`Identifiers`/`Connections`/
  `Contacts`). The tool interfaces are still English, so translating these would leave a
  reader hunting for a button that doesn't exist. Where a concept also needed a Spanish
  name, the glossary gives the Spanish term and notes the English label in parentheses.
- **The tagline** "Better Documentation | Better Data | Better Science" — treated as brand.
  If you'd rather localize it, "Mejor Documentación | Mejores Datos | Mejor Ciencia" works.
- **Blog post titles** in the Consortium Guide's reading list, since they link to English posts.

## One thing to note

`consortiumGuide.html` has a stray `</p>` before the closing `</div>` of the "core idea"
callout (around line 107 of the English file). It's harmless, and it was carried over
verbatim rather than silently fixed. Worth cleaning up in both language versions.
