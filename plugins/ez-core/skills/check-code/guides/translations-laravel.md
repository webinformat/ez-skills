# Translations — Laravel

How Laravel apps store, retrieve and sync user-facing copy.
**Read [translations.md](./translations.md) first** — source-only edits,
Crowdin sync, reuse before adding, copy vs values, placeholder naming, key
names and composed lines live there and apply to Laravel apps unchanged. This
guide maps them onto Laravel's translation system. Coding conventions for
the rest of the app are in [laravel.md](./laravel.md).

> **Scope:** Shared guide that check-code reads next to the repo's own rules.
> Examples below are **recommendations**; the active app repo may differ.
> Checked against the Laravel 13.x docs on 2026-10-13.

## Files

- Create `lang/` with `php artisan lang:publish` (new apps don't have it).
- **PHP array files** — `lang/{locale}/{file}.php`, short keys
  (`__('checkout.pay_now')`). Laravel's own strings (validation,
  pagination, auth) use this format.
- **JSON files** — `lang/{locale}.json`, keyed by the English string
  (`__('Pay now')`). Laravel recommends them for apps with many strings.
- Pick one format per app for app copy. Short keys in PHP files match the
  stable-key rule in [translations.md](./translations.md).
- Never let a JSON key equal a PHP file name: with `lang/nl/action.php`
  present and no `nl.json`, `__('Action')` returns the whole file array.
- Regional locales use ISO 15897 names with an underscore: `en_GB`, `ar_SA`
  — not `en-gb`.
- Override package strings in `lang/vendor/{package}/{locale}/` with only
  the lines that change.

## Retrieving strings

- `__('file.key')` in PHP and `{{ __('file.key') }}` in Blade.
- `trans_choice('cart.items', $count)` for plurals.
- A missing key returns the key itself. Register
  `Lang::handleMissingKeysUsing()` to log misses outside production.

## Placeholders and plurals

Laravel placeholders use `:name`, not `{name}`. The naming rules from
[translations.md](./translations.md) § Placeholder naming still apply.

```php
// lang/en/cart.php
return [
    'welcome' => 'Welcome, :name',
    'items' => '{0} Your cart is empty|{1} :count item|[2,*] :count items',
];
```

```php
__('cart.welcome', ['name' => $user->name]);
trans_choice('cart.items', $count);
```

- `:NAME` gives the value in capitals and `:Name` capitalizes it — case is a
  presentation choice, so prefer `:name` and style in the view.
- Numbers, prices, dates are **values**: pass them as replacements, never
  write digits into the string.
- `:count` is filled automatically by `trans_choice()`.

## Locale per request

- `config/app.php`: `locale` (`APP_LOCALE`), `fallback_locale`
  (`APP_FALLBACK_LOCALE`), `faker_locale` (`APP_FAKER_LOCALE`).
- Laravel has no built-in locale-detection middleware. Write one
  (`php artisan make:middleware SetLocale`) that picks the locale from the
  app's source of truth (URL segment, user setting, or
  `$request->getPreferredLanguage($supported)` for `Accept-Language`) and
  calls `App::setLocale()`.
- Always check the requested locale against an allow-list before
  `App::setLocale()`; reject or fall back on anything else.
- Read the locale with `App::currentLocale()` / `App::isLocale('ar')`.

## Validation messages

- Copy `lang/en/validation.php` per locale through the Crowdin workflow.
- `custom` holds per-field, per-rule messages; `attributes` replaces
  `:attribute` with a readable field name — fill it instead of writing
  custom messages per rule.

## Mail and notifications

- Implement `HasLocalePreference` (`preferredLocale()`) on the user model;
  Laravel then sends mail and notifications in that locale automatically.
- Override per send with `->locale('ar')` on the notification or
  `Mail::to($user)->locale('ar')`.

## Numbers, currency, dates

- `Number::format($value)` and
  `Number::currency($amount, in: 'SAR', locale: 'ar')`; set a default with
  `Number::useLocale()` in middleware next to `App::setLocale()`.
- Dates: `$date->locale(App::currentLocale())->isoFormat('LLLL')` or
  `->diffForHumans()` (Carbon).

## Right-to-left locales

- Set `dir="rtl"` and `lang` on `<html>` from the current locale in the
  layout; never set base direction with CSS.
- Use logical CSS properties (`margin-inline-start`, `text-align: start`)
  so one stylesheet serves both directions.

## Database content

UI copy goes through `lang/`; translatable **database** content (product
names, CMS pages) needs per-record translations. A common choice is
`spatie/laravel-translatable`, which stores translations as JSON in the
model's column (community package).

## Crowdin

- Crowdin reads PHP and JSON translation files natively.
- `crowdin.yml` follows Laravel's layout. Example — adjust to the app:

  ```yaml
  files:
    - source: /lang/en/*.php
      translation: /lang/%locale_with_underscore%/%original_file_name%
    - source: /lang/en.json
      translation: /lang/%locale_with_underscore%.json
  ```

  `%locale_with_underscore%` gives `ar_SA`; use `%two_letters_code%` for
  plain language folders (`ar`). Map Crowdin language codes in the project's
  Language Mapping when they differ from the app's folder names.
- Edit only the files listed under `source` — see
  [translations.md](./translations.md) § Before editing.

## Anti-patterns (smells to flag)

1. Separate keys per region or number (`items_30`, `items_ksa`) → one key
   with `:count` / named placeholders.
2. Hand-edited target locale files (`lang/ar/…`) → change the English
   source; Crowdin brings the translations.
3. `App::setLocale($request->lang)` without an allow-list → validate first.

## Further reading

1. [Laravel — Localization](https://laravel.com/docs/localization)
2. [Laravel — Notifications](https://laravel.com/docs/notifications)
3. [Laravel — Helpers (Number)](https://laravel.com/docs/helpers)
4. [Translator API — handleMissingKeysUsing](https://api.laravel.com/docs/13.x/Illuminate/Translation/Translator.html)
5. [Carbon](https://github.com/CarbonPHP/carbon)
6. [W3C — Structural markup and right-to-left text](https://www.w3.org/International/questions/qa-html-dir)
7. [Crowdin — Configuration file](https://support.crowdin.com/developer/configuration-file/)
8. [spatie/laravel-translatable](https://spatie.be/docs/laravel-translatable/v6/introduction) (community)
