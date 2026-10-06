# Privacy

FCMO AI Newsletter is a static public publication with optional FCMO AI Newsletter email subscriptions. Reading the newspaper does not require an account. Signup is enabled only when the selected email provider is configured. The form sends the email address, chosen language and explicit consent to that service; the static newspaper stores no subscriber database.

## Optional FCMO AI Newsletter email

The operator selected Kit for the initial hosted FCMO AI Newsletter route on 2026-10-05. `FCMO_EMAIL_PROVIDER` selects the form and delivery adapter. Kit signup posts directly to Kit’s public form, with a separate form for EN/es-419/zh-Hans, an unchecked required consent checkbox and email confirmation configured in Kit. Form membership is the default delivery filter; tags are optional. The checkbox is enforced by the browser; our service does not receive or enforce Kit form submissions. The Kit notice in `legal/email-privacy-kit.json` is rendered in all three languages when Kit is selected. It describes Kit processing, GitHub Actions encrypted backups, configured retention and the complete public controller notice supplied by `FCMO_EMAIL_PRIVACY_URL`. A real postal address/contact, provider terms, transfer arrangements and disabled tracking must be in place before activation. Kit’s consent/retention features must be confirmed with the real account; L26’s gateway retention guarantees do not automatically apply to Kit.

Brevo is an alternative hosted provider selected by configuration. Its three public form actions submit directly to Brevo, with the `EMAIL` field and a required unchecked browser consent checkbox. Each form must use Brevo’s double opt-in flow and add contacts to its locale list only after confirmation. The site exposes no API key or server of ours. The selected notice `legal/email-privacy-brevo.json` describes Brevo and encrypted GitHub Actions backups in EN/es-419/zh-Hans. Provider enforcement, final hosted-form fields, consent records, suppression, disabled tracking, retention and account-specific transfer terms require verification before activation; no L26 host retention guarantee is asserted for Brevo.

Daily adapter exports contain language memberships and all available subscription states, including suppression. Plaintext exists only in runner memory and the pipe to age; only ciphertext is written and uploaded, with 30-day artifact retention. The decryption key is held separately and never placed in GitHub. An export is private audience data even when the newspaper repository is public. Kit/Brevo export completeness, language assignments and suppression must be checked live before treating the backup as migration-ready.

The following operational guarantees describe the retained Listmonk + SES route:

Matías Peña Szőke is responsible for subscription data. The complete notice at the configured email service’s `/privacy` includes the actual postal address and monitored rights contact; it must be complete before activation. The source-controlled EN/es-419/zh-Hans notice is `legal/email-privacy.json` and the paper generator renders it on all three privacy routes.

Listmonk holds subscriber addresses, list membership, confirmation metadata and delivery/bounce state on the private host. Amazon Web Services SES processes delivery. Processor terms and applicable international-transfer safeguards must be arranged before the operator sets `FCMO_EMAIL_COMPLIANCE_READY=true`. No addresses are sold; individual/open/click tracking is disabled. Membership in the FCMO AI Newsletter does not subscribe readers to Javier’s Letters.

Signup requires an unchecked consent box and double opt-in. Every FCMO AI Newsletter email has a recipient-specific unsubscribe link and RFC 8058 one-click headers, without a fee or login. Access, rectification, cancellation/deletion, objection, withdrawal, portability and limits on processing can be requested through the complete notice’s rights contact. Listmonk also provides profile export and deletion.

The daily maintenance unit expires unconfirmed memberships after 30 days and deletes orphaned subscriber profiles. Consent and rate-limit records use keyed hashes rather than clear email/IP data and expire after 30 days. Confirmation records remain while subscribed. Minimal unsubscribe/bounce suppression may remain to prevent further sends; readers can request deletion. Encrypted rolling backups expire after 30 days. A working backup timer and separately held decryption key are activation prerequisites.

## Hosting and technical data

The site is hosted using GitHub Pages. As with normal web hosting, GitHub may process technical information needed to deliver and secure the service, such as network requests, IP addresses, device or browser information, and related logs, under GitHub's own terms and privacy practices.

## Analytics, cookies, and third-party services

The publication should not claim to be tracker-free if analytics, embedded media, subscription tools, forms, advertising, or other third-party services are later added. Any such addition must be reviewed and this notice updated before deployment where it materially changes data handling.

FCMO AI Newsletter should avoid non-essential tracking by default.

## External links

Articles may link to third-party websites. Those sites control their own data practices, and their privacy policies apply when readers visit them.

## Changes

This notice may be updated as the publication gains new features. Material changes to reader data collection should be reflected here before or at the same time the relevant feature is published.

Last updated: October 6, 2026.
