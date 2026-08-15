# 🎬 Bonifade Technologies — Content Generation Playbook

How we create content that sells: blogs, videos, and picture posts with
writeups. Owned by Marketer 2 (Content) and Marketer 3 (Growth/Creative);
research feeds from Marketer 1. Storytelling framework from
**Sell with a Story — Paul Smith** (`library/parsed/`).

---

## The 5-Step Content Workflow

### 1. Study the product
Before any content: read the product's file in **`products/`** (the single
source of truth for what we sell), use the product (or its demo),
list what it *actually does* and for whom. No content from guesses.
Output: 5-bullet product truth sheet (what it is, who it's for, the one
thing it does best, proof points, price).

### 2. Research the pain (online listening)
Find the **issues people are actually facing** related to this product:
- Search Nairaland, Reddit, X/Twitter, Facebook groups, Quora, competitor
  reviews, WhatsApp/Telegram community complaints (Firecrawl tools)
- Capture REAL phrases people use — their words become our script lines
- Output: top 3 pain points, each with 2–3 verbatim quotes + source links

### 3. Choose the story (most important step — Paul Smith)
> "It is far better to tell the right story in a mediocre fashion than to
> tell the wrong story with a stunning performance."
Pick a story where the **audience sees themselves**: a relatable hero
(someone like them), facing the same challenge they face right now.
Every story needs Smith's 4 elements:
- **A hero we care about** (a Nigerian business owner like our buyer)
- **A villain we're afraid of** (the pain: lost sales, manual chaos, downtime)
- **An epic struggle** (trying and failing with the wrong solutions)
- **A worthy lesson** (the thing we want them to learn/do)

### 4. Write the video — sequence by sequence
Structure per **Smith's 7-step model**: Hook → Context → Challenge →
Conflict → Resolution → Lesson → Action.

**60-second template:**
| Seq | Time | Story step | Content |
|-----|------|-----------|---------|
| 1 | 0:00–0:05 | HOOK | Pattern interrupt: the pain in THEIR words ("Your customers are messaging you on WhatsApp… and you're losing half of them") |
| 2 | 0:05–0:15 | CONTEXT | Introduce the hero: "Ada runs a logistics company in Lagos…" |
| 3 | 0:15–0:25 | CHALLENGE | What she wanted vs what stood in the way |
| 4 | 0:25–0:40 | CONFLICT | The struggle: what she tried, why it failed (the villain at work) |
| 5 | 0:40–0:50 | RESOLUTION | What changed — the product enters naturally, not as an ad |
| 6 | 0:50–0:55 | LESSON | The one line they remember ("Your business doesn't need more effort. It needs a system.") |
| 7 | 0:55–1:00 | ACTION | One CTA: "Book a free clarity session — link below." |

**90-second version**: same 7 sequences; give Seq 1 +3s, Seq 2 +5s,
Seq 4 +10s (conflict is where emotion lives), Seq 5 +8s, Seq 6 +4s.
**Never exceed 1:30.**

Script deliverable format per sequence: `VISUAL (what we see) | AUDIO/VO
(exact words) | TEXT OVERLAY | ENGINE (HeyGen avatar / Veo clip / screen
recording)`.

### 5. Produce & multiply
- **Video**: HeyGen (presenter/storyteller on screen) or Veo (cinematic
  visuals of the story) or hybrid (avatar narration + Veo b-roll),
  assembled with ffmpeg/Remotion. Store in R2.
- **Blog post**: expand the same story to 600–900 words, SEO-titled
  around the pain ("how Nigerian businesses lose customers on WhatsApp"),
  embed the video.
- **Picture post + writeup**: Stitch banner of the lesson line + the story
  condensed to 100 words for X/LinkedIn/Facebook/Instagram.
One story = video + blog + 3 picture posts. Never create once, publish once.

---

## Storytelling rules (from Sell with a Story — follow them all)
- **Emotion is mandatory**: "The king died, then the queen died" is a fact;
  "the queen died *of grief*" is a story. Facts tell, emotions sell.
- **Surprise**: move one key piece of information from the context to the
  end of the story.
- **Withhold, don't announce**: let the audience figure out the context
  themselves — a mystery they solve is more engaging than a fact you state.
- **Dialogue and sensory detail** over summary: "She stared at 47 unread
  WhatsApp messages at 11pm" beats "she was overwhelmed".
- **The product is NOT the hero** — the customer is. The product is the
  weapon the hero picks up.
- **Never stretch the truth**: real client stories only (with permission,
  via Legal), or clearly composite stories told honestly.

## 🇳🇬 Nigeria first, then the world
- **Nigerian resonance FIRST**: set stories in real Nigerian life — Lagos
  traffic, NEPA/light and generators, data costs, POS transfers, WhatsApp
  Business, Naira pricing, Nairaland culture, "no gree for anybody" energy.
  Use real names, real cities, naira figures.
- **Language**: plain English with Nigerian warmth; Pidgin lines where they
  land naturally ("How you wan take manage 200 customers with notebook?").
- **Global adaptation**: same story skeleton, swap the setting (Lagos →
  London/Nairobi/Toronto), currency, and local references. The struggle is
  universal; only the scenery changes. HeyGen translation for other languages.
- **Test order**: launch in Nigeria, learn, then adapt the winner globally —
  not the reverse.

## 🎯 Ads Creation — Two Ad Types

### Type 1: Story Ads
The full 5-step workflow above — Paul Smith storytelling, 60s/90s videos.
Use for: brand building, launches, retargeting warm audiences.

### Type 2: Feature & Offer Ads (the Akin Alabi method)
Shorter, direct ads — **a product feature CAN be the ad**, but never as a
bare feature+price list. Rules from **How to Sell to Nigerians** and
**Small Business Big Money** (`library/parsed/`):

- **Never advertise product + price.** "What most people do when they
  advertise is list their products and their prices. That is why most people
  do not succeed." Every ad must carry an **irresistible offer** — "if you
  cannot answer 'what is the crazy offer?', do not advertise yet."
- **Bonuses beat discounts.** Alabi's seminar: ₦15k ticket, zero attendees.
  Same seminar + free 3-month consulting + free eBooks/software, price
  *raised* to ₦25k — sold out with people begging at the door. Stack value
  instead of cutting price. (Same doctrine as Hormozi's $100M Offers.)
- **One feature per ad**, translated into a fear/desire angle: not "automated
  invoicing" but "stop chasing payments like a debtor — invoices that follow
  up by themselves."
- **The 2% rule — capture before you sell.** Only ~2% buy on first contact;
  the other 98% are gone forever unless you capture them. Cold-traffic ads
  should often offer a free educational piece (guide, audit, checklist) in
  exchange for contact details → into the leads DB → nurture via email.
- **Build the list.** "Once you have a list, you will never go broke."
  Every ad either sells or captures — preferably captures, then email sells.
- **Fear factor, honestly.** Nigerians have been burned (MMM, wonder banks).
  Legitimate fear angles work: what they LOSE by not acting — lost customers,
  lost data, lost money. Never manufacture fake urgency; Legal reviews claims.
- **Format**: 15–30s video (HeyGen/Veo), Stitch banner + 60-word writeup, or
  carousel. CTA always to ONE action (book, download, or WhatsApp us).

### Quick reference — which type when
| Situation | Ad type |
|-----------|---------|
| Cold audience, brand new | Feature/offer ad with free-value capture |
| Warm audience (engaged before) | Story ad |
| Retargeting / abandoned | Story ad (testimonial) + offer reminder |
| New feature launch | Feature ad (one feature + offer) |

## Quality bar before anything ships
1. Would the target buyer see THEMSELVES in the hero? (If not, rewrite)
2. Is the pain quote real (from step 2 research)?
3. Is it ≤ 60s or ≤ 90s? (Cut, never compress)
4. Emotion present? Surprise present? One clear CTA?
5. For offer/feature ads: is there a **crazy offer**? (No offer = don't run it)
6. Does it sell OR capture contact details? (Preferably capture for cold traffic)
7. Legal review passed (claims, client permissions)?
