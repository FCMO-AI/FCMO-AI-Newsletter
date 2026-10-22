# Studio dogfood battery

Drives a throwaway Studio instance as a person would (login, essay with figure, pull quote and
footnote, save and reload, translation, preview, publish screen, Matías on a phone, error states)
at 1440x900 and 390x844, light and dark. Never point it at the live instance.

```sh
# throwaway instance: own STUDIO_DATA, random STUDIO_SESSION_KEY, STUDIO_PORT=8497, two users added with Auth.add_user
export PW_JAVIER=... PW_MATIAS=... FRAMES=/var/tmp/frames FIGURE=/path/any.png
node write-battery.mjs after http://127.0.0.1:8497   # prints SLUG per config
SLUG=<slug> node flow-battery.mjs after http://127.0.0.1:8497
```

Needs `playwright` resolvable from the working directory. Screenshots stay out of the repository.
`h-errors` fails if a double click on «Empezar a escribir» creates two pieces or if an expired
session lands on a login screen without the explanation.
