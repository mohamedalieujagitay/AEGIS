<!--
Title: use Conventional Commits, for example "feat(recon): implement DNS record discovery".
A CI check validates the title. See CONTRIBUTING.md sections 5 and 6.
One feature, fix or documentation change per pull request.
-->

## Summary

<!-- What changed and why. -->

Refs #<!-- issue number, or remove this line -->

## Changes

<!-- Files and modules affected. -->

-

## Decisions

<!-- Architectural or technical decisions made, with links to DECISIONS.md entries. Write "None" if there are none. -->

## Security implications

<!--
Describe the effect on authentication, authorization, workspace isolation,
scope enforcement, SSRF protection, worker isolation, result ingestion,
secrets or logging. Write "None" with a short reason if there is no effect.
-->

## Tests

<!-- Commands you ran and their results. Do not report tests you did not run. -->

-

## Known limitations

<!-- Write "None" if there are none. -->

## Checklist

- [ ] The title follows Conventional Commits.
- [ ] The change is limited to one feature, fix or documentation update.
- [ ] Tests cover new behaviour, including failure paths for security-sensitive code.
- [ ] Backend checks pass: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, `pytest`.
- [ ] Frontend checks pass: `npm run check`, `npm test`, `npm run build`.
- [ ] Documentation affected by the change is updated.
- [ ] Database schema changes include a reviewed Alembic migration.
- [ ] New or changed dependencies are justified and recorded in `THIRD_PARTY_NOTICES.md`.
- [ ] Backend dependency changes regenerate **both** `requirements-dev.lock` and `requirements.lock` (CONTRIBUTING.md section 2); frontend changes update `package-lock.json`.
- [ ] No secrets, credentials, private keys, `.env` files or local tool configuration are included.
