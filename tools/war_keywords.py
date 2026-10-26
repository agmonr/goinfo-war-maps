"""ONE keyword list for the war rules (the owner 10-26: "each of these verbs IS a battle"). Imported by test_war_battles (R35), test_war_heavy_losses (R34), test_war_stopped (R49/R50), war_stopped.
Families: BATTLE (a card that names a fight must show one), STOPPED (נבלם: the force was fought to a standstill = destroyed, units stop dead, wrecks), HOLD (בולמת: a defender holds an attacker in place, both sides take heavy losses),
SUPREME (מאמץ עליון / בכל הכוח / במחיר כבד: very heavy casualty level). Hebrew letters may not stand next to a match (no prefix/suffix hits). "נעצרת בפקק" (a traffic jam) is NOT a stop: STOPPED needs a fire/enemy word after נעצר."""
import re
NB = r'(?<![א-ת])(?:%s)(?![א-ת])'
def fam(words): return re.compile(NB % '|'.join(words))
BATTLE_WORDS = ['קרב', 'קרבות', 'קרבי', 'מתקפה', 'מתקפת', 'התקפה', 'התקפת', 'תקף', 'תקפו', 'תוקף', 'תוקפים', 'הסתערות', 'פשיטה', 'פשט', 'הפגזה', 'הפגיז', 'מפגיזות', 'מפגיז', 'התנגשות', 'לחימה', 'ננעל', 'הדיפת', 'נהדפת', 'נהדפה', 'נהדפו',
                'כיבוש', 'כבש', 'כבשו', 'כובש', 'כובשת', 'כובשים', 'מארב', 'נבלם', 'נבלמה', 'נבלמו', 'נבלמים', 'נבלמת', 'נבלמות', 'בולמת', 'בולם', 'בולמים', 'בלמה', 'בלמו', 'בלם', 'נהדף', 'הושמד', 'הושמדה', 'הושמדו', 'לבלום', 'מאמץ עליון', 'במחיר כבד', 'בכל הכוח', 'לכיבוש', 'בכיבוש', 'להשתלט', 'השתלט', 'השתלטות', 'השתלטו', 'נופל בידי', 'נפל בידי', 'נפלה בידי', 'נפלו בידי', 'ניסיון כיבוש']
BATTLE = fam(BATTLE_WORDS)
STOPPED = re.compile(r'(?<![א-ת])(?:נבלם|נבלמה|נבלמו|נבלמים|נבלמת|נבלמות)(?![א-ת])|(?<![א-ת])נעצר(?:ה|ו)?\s+(?:באש|על ידי|על־ידי|בידי|מול|בכוח)')
HOLD = re.compile(r'(?<![א-ת])(?:בולמת|בולם|בולמים|בלמה|בלמו|בלם|לבלום|לבלם)(?![א-ת])|(?<![א-ת])(?:עצרה|עצרו|עצר|מנעה|מונעת)\s+(?:את\s+)?(?:ה)?התקדמות')
SUPREME = re.compile(r'מאמץ עליון|בכל הכוח|במחיר כבד|המחיר היה כבד')
def hits(text):
    return {k: bool(v.search(text)) for k, v in (('stopped', STOPPED), ('hold', HOLD), ('supreme', SUPREME))}
