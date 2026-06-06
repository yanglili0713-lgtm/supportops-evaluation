from __future__ import annotations

from dataclasses import asdict, dataclass


SUPPORTED_INTENTS = {
    "login_issue",
    "billing_refund",
    "api_key_issue",
    "rag_upload_issue",
    "permission_issue",
    "deployment_error",
    "general_faq",
    "unknown",
}


@dataclass(frozen=True)
class RouterResult:
    intent: str
    confidence: float
    reason: str
    matched_keywords: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


KEYWORD_RULES: dict[str, list[tuple[str, float]]] = {
    "login_issue": [
        ("登录态过期", 4.0),
        ("登录失败", 3.5),
        ("无法登录", 3.5),
        ("登不上", 3.0),
        ("session expired", 4.0),
        ("login failed", 3.5),
        ("login", 1.5),
        ("验证码", 1.2),
        ("密码", 1.2),
    ],
    "billing_refund": [
        ("退款", 4.0),
        ("发票", 3.5),
        ("账单", 3.5),
        ("扣费", 3.0),
        ("支付", 2.0),
        ("invoice", 3.5),
        ("billing", 3.5),
        ("refund", 4.0),
        ("charge", 2.0),
    ],
    "api_key_issue": [
        ("api key", 4.5),
        ("apikey", 4.5),
        ("key 失效", 4.0),
        ("密钥失效", 4.0),
        ("api 密钥", 4.0),
        ("401", 1.8),
        ("unauthorized", 2.2),
        ("invalid key", 4.0),
        ("鉴权失败", 2.2),
    ],
    "rag_upload_issue": [
        ("上传 pdf", 4.5),
        ("上传pdf", 4.5),
        ("pdf", 2.5),
        ("检索不到", 4.0),
        ("搜不到", 3.0),
        ("召回不到", 3.0),
        ("知识库", 2.0),
        ("rag", 2.0),
        ("embedding", 1.5),
        ("chunk", 1.5),
        ("索引", 1.5),
    ],
    "permission_issue": [
        ("权限不足", 4.0),
        ("没有权限", 4.0),
        ("无权限", 4.0),
        ("permission denied", 4.0),
        ("forbidden", 3.0),
        ("403", 2.5),
        ("团队权限", 3.5),
        ("角色", 1.5),
        ("成员", 1.2),
    ],
    "deployment_error": [
        ("部署失败", 4.0),
        ("部署报错", 4.0),
        ("接口报错", 3.5),
        ("服务启动失败", 3.5),
        ("500", 2.0),
        ("timeout", 2.0),
        ("超时", 2.0),
        ("deployment", 3.5),
        ("deploy", 3.0),
        ("error code", 2.0),
    ],
    "general_faq": [
        ("怎么使用", 2.0),
        ("如何使用", 2.0),
        ("文档", 1.5),
        ("价格", 1.5),
        ("支持哪些", 2.0),
        ("是什么", 1.5),
        ("faq", 2.0),
        ("how to", 2.0),
    ],
}


def route_question(question: str) -> dict:
    """Route a support question to a small, explainable intent schema."""
    return route_intent(question).to_dict()


def route_intent(question: str) -> RouterResult:
    text = _normalize(question)
    if not text:
        return _unknown("empty question")

    scores: dict[str, float] = {}
    matches: dict[str, list[str]] = {}
    for intent, rules in KEYWORD_RULES.items():
        for keyword, weight in rules:
            if _contains_keyword(text, keyword):
                scores[intent] = scores.get(intent, 0.0) + weight
                matches.setdefault(intent, []).append(keyword)

    if not scores:
        return _unknown("no router keyword matched")

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_intent, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = _confidence(best_score, second_score)

    if confidence < 0.35:
        return _unknown("matched keywords were too weak")

    matched_keywords = matches[best_intent]
    reason = (
        f"matched {best_intent} with score {best_score:.1f}; "
        f"keywords: {', '.join(matched_keywords)}"
    )
    return RouterResult(
        intent=best_intent,
        confidence=confidence,
        reason=reason,
        matched_keywords=matched_keywords,
    )


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = _normalize(keyword)
    compact_text = text.replace(" ", "")
    compact_keyword = normalized_keyword.replace(" ", "")
    return normalized_keyword in text or compact_keyword in compact_text


def _confidence(best_score: float, second_score: float) -> float:
    base = min(0.95, 0.25 + best_score / (best_score + 4.0) * 0.75)
    margin = max(0.0, best_score - second_score)
    penalty = 0.15 if second_score and margin < 2.0 else 0.0
    return round(max(0.0, base - penalty), 2)


def _unknown(reason: str) -> RouterResult:
    return RouterResult(
        intent="unknown",
        confidence=0.0,
        reason=reason,
        matched_keywords=[],
    )
