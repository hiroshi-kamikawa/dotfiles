---
name: hk-setup-astro
description: "Set up or audit a minimal Astro starter with Git, Tailwind CSS, daisyUI, Partytown, and Sitemap. Use when creating this starter from scratch, reproducing the standard setup, or checking that an existing project matches the expected configuration."
---

# HK Setup Astro

Create or audit a minimal Astro project that uses pnpm, Tailwind CSS 4, daisyUI 5, Partytown, and Sitemap. Preserve unrelated files and existing project choices.

## Choose the Mode

- Use **setup mode** when the target directory is empty or the user explicitly asks to create the starter.
- Use **audit mode** when an Astro project already exists or the user asks whether setup is correct.
- If the directory contains unrelated files but is not an Astro project, inspect them and ask before scaffolding into it.

## Setup Mode

1. Resolve the intended project directory and inspect its contents.
2. For an empty directory, run `bash "<skill-root>/scripts/bootstrap.sh" "<project-directory>"`. The script safely refuses non-empty targets, scaffolds the minimal project, initializes Git only when needed, and installs Tailwind, daisyUI, Partytown, and Sitemap.
3. If current CLI behavior differs from the script, inspect official documentation and update the generated project deliberately. Do not bypass the script's non-empty-directory guard.
4. Set Astro's `site` option from `SITE_URL`, with `http://localhost:4321` as the local fallback. Add `.env.example` with `SITE_URL=https://example.com`, and tell the user to set the real deployed origin in production. Do not invent or hard-code an unverified production domain.
5. Ensure `tsconfig.json` extends the Astro strict configuration and includes these compiler options, merging them with any existing project-specific options:

   ```json
   {
     "compilerOptions": {
       "baseUrl": ".",
       "noUnusedLocals": true,
       "noUnusedParameters": true,
       "paths": {
         "@/*": ["./src/*"]
       }
     }
   }
   ```

6. Ensure the Tailwind stylesheet contains these directives:

   ```css
   @import "tailwindcss";
   @plugin "daisyui";
   ```

7. Ensure the stylesheet is imported exactly once from a shared layout. If the minimal starter has no layout, import it from `src/pages/index.astro`. Do not create a layout solely for this import.
8. Run `python3 "<skill-root>/scripts/astro_starter.py" audit "<project-directory>"` and resolve every missing or inconsistent result.
9. Run the verification workflow. If CSS optimization warns about the unused daisyUI Calendar selector `:hover:not(selected, today)`, confirm that no supported calendar component is used, then change the plugin block to:

   ```css
   @plugin "daisyui" {
     exclude: calendar;
   }
   ```

   Do not exclude Calendar when the project uses Cally, React Day Picker, Pikaday, or Vanilla Calendar Pro. Do not suppress unrelated warnings.

## Audit Mode

Run `python3 "<skill-root>/scripts/astro_starter.py" audit "<project-directory>"` before changing anything. Treat its output as a deterministic first pass, then inspect the project to confirm stylesheet reachability and context-dependent Calendar usage. The script checks all of the following:

- `package.json` uses Astro and declares `@tailwindcss/vite`, `tailwindcss`, `daisyui`, `@astrojs/partytown`, and `@astrojs/sitemap`.
- The package manager and lockfile are pnpm-based.
- `astro.config.mjs` imports `@tailwindcss/vite` and registers `tailwindcss()` in `vite.plugins`.
- `astro.config.mjs` imports and registers both Partytown and Sitemap.
- Astro's `site` option resolves from `SITE_URL`, uses only a local development URL as a fallback, and has a documented production value in `.env.example`.
- `tsconfig.json` extends the Astro strict configuration and sets `baseUrl` to `.`, enables `noUnusedLocals` and `noUnusedParameters`, and maps `@/*` to `./src/*`.
- A project stylesheet imports `tailwindcss` and registers the `daisyui` plugin.
- A Calendar exclusion is present only when the Calendar component is unused and the installed daisyUI version emits the known selector warning.
- The stylesheet is reachable from every intended page through a page or shared layout import.
- A Git work tree exists when Git initialization is part of the request.
- No obsolete Tailwind 3 configuration is being mistaken for the Tailwind 4 Vite setup.

Report each check as pass, missing, or inconsistent. In audit-only requests, do not modify files. When the user asks to repair the setup, make only the changes needed to resolve failed checks, then verify again.

## Verification

1. Run `python3 "<skill-root>/scripts/astro_starter.py" verify "<project-directory>" --run-build --site-url "https://example.test"`. This runs the production build and checks Sitemap and Partytown output.
2. Run the project's type-checking or Astro checking script when available; otherwise run `pnpm exec astro check` when the required checker is installed. Confirm the `tsconfig.json` options and path alias are accepted.
3. Confirm the build succeeds and its output shows daisyUI loading.
4. Review the script's confirmation that the build creates `sitemap-index.xml`, at least one numbered sitemap file, and the safe test origin in both.
5. Review the script's confirmation that generated HTML contains the Partytown bootstrap and output contains the `~partytown` assets. When third-party scripts are in scope, mark only compatible scripts with `type="text/partytown"` and configure `forward` for required main-thread globals.
6. Confirm the final build has no daisyUI Calendar selector warning. If the warning remains, investigate the installed daisyUI and Tailwind versions instead of filtering build output.
7. Inspect the final dependency and configuration diff.
8. Report:
   - setup or audit mode used;
   - installed package versions from the resolved project state;
   - files created or changed;
   - build result;
   - Partytown asset and Sitemap XML verification;
   - whether `SITE_URL` still needs the real production origin;
   - any skipped or unavailable check.

Do not claim success from package installation alone. Treat a successful production build as the minimum functional verification.

## Safety and Portability

- Follow the project's instruction files before changing the project.
- Use the package manager already established by the project; use pnpm for a new starter.
- Do not remove or recreate an existing project to force it into the expected shape.
- Do not reinitialize an existing Git repository.
- Ask before overwriting conflicting configuration or scaffolding into a non-empty, unrelated directory.
- Use current CLI output and resolved package metadata instead of hard-coding package versions.
- Consult official Astro, Tailwind CSS, and daisyUI documentation when commands or generated configuration differ from this workflow.
- Resolve `<skill-root>` from the directory containing this `SKILL.md`; never assume the current working directory.
- Prefer the bundled scripts for their documented operations. Keep semantic decisions, conflicting-file edits, warning diagnosis, and final diff review in the agent workflow.
