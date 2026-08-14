from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyRule:
    category: str
    patterns: tuple[re.Pattern[str], ...]


def _compile(*patterns: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)


# MiniMax H3 Acceptable Use Policyのうち、プロンプト文字列から高い確度で
# 検出できる代表的な違反を拒否する。これは完全なモデレーションではないため、
# 利用条件への同意、権利確認、通報・停止手順と組み合わせて運用する。
RULES = (
    SafetyRule(
        "minors_exploitation",
        _compile(
            r"\b(child|minor|underage|schoolgirl|schoolboy)\b.{0,40}\b(nude|naked|sexual|sex|porn|erotic)\b",
            r"\b(nude|naked|sexual|sex|porn|erotic)\b.{0,40}\b(child|minor|underage|schoolgirl|schoolboy)\b",
            r"児童.{0,20}(性的|裸|わいせつ|ポルノ)",
            r"(未成年|小学生|中学生).{0,20}(性的|裸|わいせつ|ポルノ)",
        ),
    ),
    SafetyRule(
        "nonconsensual_impersonation",
        _compile(
            r"\b(deepfake|impersonat(?:e|ion)|face[ -]?swap)\b.{0,50}\b(without consent|nonconsensual|fraud|scam|deceive)\b",
            r"\b(without consent|nonconsensual|fraud|scam|deceive)\b.{0,50}\b(deepfake|impersonat(?:e|ion)|face[ -]?swap)\b",
            r"(本人の同意なく|無断で|なりすまし|詐欺).{0,40}(顔交換|ディープフェイク|本人そっくり|実在人物)",
            r"(顔交換|ディープフェイク|本人そっくり|実在人物).{0,40}(本人の同意なく|無断で|なりすまし|詐欺)",
        ),
    ),
    SafetyRule(
        "self_harm_or_harm",
        _compile(
            r"\b(step[- ]by[- ]step|instructions?|how to)\b.{0,50}\b(suicide|self[- ]harm|kill myself|poison someone)\b",
            r"\b(suicide|self[- ]harm|kill myself|poison someone)\b.{0,50}\b(step[- ]by[- ]step|instructions?|how to)\b",
            r"(自殺|自傷|人を毒殺).{0,30}(方法|手順|やり方|指南)",
            r"(方法|手順|やり方|指南).{0,30}(自殺|自傷|人を毒殺)",
        ),
    ),
    SafetyRule(
        "violent_extremism",
        _compile(
            r"\b(terrorist|terrorism|violent extremis(?:m|t))\b.{0,50}\b(propaganda|recruit|glorif|instruction|attack plan)\b",
            r"\b(propaganda|recruit|glorif|instruction|attack plan)\b.{0,50}\b(terrorist|terrorism|violent extremis(?:m|t))\b",
            r"(テロ|暴力的過激主義).{0,30}(宣伝|勧誘|称賛|攻撃計画|実行手順)",
        ),
    ),
    SafetyRule(
        "election_deception",
        _compile(
            r"\b(fake|fabricated|false)\b.{0,30}\b(election|ballot|candidate)\b.{0,40}\b(influence|mislead|deceive|suppress)\b",
            r"(選挙|候補者|投票).{0,30}(虚偽|偽情報|捏造).{0,30}(誘導|妨害|影響)",
        ),
    ),
    SafetyRule(
        "false_engagement_or_harassment",
        _compile(
            r"\b(fake reviews?|fake engagement|bot engagement)\b",
            r"\b(targeted harassment|defame|doxx(?:ing)?)\b",
            r"(偽レビュー|サクラレビュー|偽エンゲージメント|組織的嫌がらせ|誹謗中傷用)",
        ),
    ),
    SafetyRule(
        "personal_data_harm",
        _compile(
            r"\b(doxx(?:ing)?|leak personal (?:data|information)|publish home address)\b",
            r"(個人情報|住所|電話番号).{0,30}(晒す|暴露|漏えい|嫌がらせ)",
        ),
    ),
    SafetyRule(
        "malware",
        _compile(
            r"\b(ransomware|malware)\b.{0,40}\b(deploy|spread|infect|payload|damage)\b",
            r"\b(deploy|spread|infect|payload|damage)\b.{0,40}\b(ransomware|malware)\b",
            r"(ランサムウェア|マルウェア).{0,30}(拡散|感染|攻撃|破壊)",
        ),
    ),
    SafetyRule(
        "high_risk_automated_decision",
        _compile(
            r"\b(automatically decide|automated decision)\b.{0,50}\b(credit|employment|housing|insurance|medical|immigration|law enforcement)\b",
            r"(自動判定|自動決定).{0,40}(採用|解雇|融資|保険|住宅|医療|移民|逮捕)",
        ),
    ),
    SafetyRule(
        "military_use",
        _compile(
            r"\b(military targeting|military operation plan|weapon targeting system|combat mission planning)\b",
            r"(軍事標的|軍事作戦計画|兵器照準|戦闘任務計画)",
        ),
    ),
    SafetyRule(
        "unlicensed_professional_activity",
        _compile(
            r"\b(pretend to be|impersonate)\b.{0,30}\b(doctor|lawyer|financial adviser)\b.{0,40}\b(advice|consultation|diagnosis)\b",
            r"(無資格|資格がない).{0,30}(診断|法律相談|投資助言|医療行為)",
        ),
    ),
)


def blocked_h3_categories(prompt: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", prompt).casefold()
    return [
        rule.category
        for rule in RULES
        if any(pattern.search(normalized) for pattern in rule.patterns)
    ]
