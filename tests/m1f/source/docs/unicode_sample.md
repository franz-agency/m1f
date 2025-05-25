# Unicode Character Testing File

This file contains various Unicode characters to test encoding handling:

## International Characters

- German: Grüße aus München! Der Fluß ist schön.
- French: Voilà! Ça va très bien, merci.
- Spanish: ¿Cómo estás? Mañana será un día mejor.
- Russian: Привет, как дела? Хорошо!
- Chinese: 你好，世界！
- Japanese: こんにちは世界！
- Arabic: مرحبا بالعالم!
- Greek: Γεια σου Κόσμε!
- Emojis: 😀 🚀 🌍 🎉 🔥 👨‍💻

## Special Unicode Symbols

- Mathematical: ∑ ∫ ∏ √ ∞ ∆ ∇ ∂ ∀ ∃ ∈ ∉ ∋ ∌
- Currency: € £ ¥ ¢ $ ₹ ₽
- Arrows: → ← ↑ ↓ ↔ ↕ ⇒ ⇐ ⇔
- Miscellaneous: © ® ™ ° § ¶ † ‡ • ⌘ ⌥
- Technical: ⌚ ⌨ ✉ ☎ ⏰

## Test cases for file system path handling

- Windows paths: C:\Users\User\Documents\Résumé.pdf
- Unix paths: /path/to/documents/résumé.pdf
- URLs: https://example.com/üñïçødé/test?q=値&lang=日本語

## Test cases for escaping

- Backslashes: \\ \n \t \r \u1234
- HTML entities: &lt; &gt; &amp; &quot; &apos;
- JavaScript escaped: \u{1F600} \u0041 \x41

## Test cases with BOM and other special characters

Zero-width spaces and non-breaking spaces below:

- [​] (zero-width space between brackets)
- [ ] (non-breaking space between brackets)
- Control characters test: test
