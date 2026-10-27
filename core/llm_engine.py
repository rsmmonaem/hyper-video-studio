#!/usr/bin/env python3
"""
Hyper Video Studio - Multi-LLM Engine & Blueprint Planner
Supports:
1. 'template' : 100% Free, zero-API cost blueprint generator with proven viral developer topics.
2. 'gemini'   : Google Gemini API (Gemini 2.5/3.0 / Flash / Pro).
3. 'openai'   : OpenAI GPT-4o / GPT-4o-mini.
4. 'openrouter' / 'custom' : Any OpenAI-compatible endpoint (OpenRouter, OmniRouter, Ollama, DeepSeek).
"""

import os
import json
import random
import urllib.request
import urllib.error

# High-Retention Architectural & Engineering Blueprints (Zero-Cost Offline Fallback)
CURATED_BLUEPRINTS = [
    {
        "category": "High Concurrency & Load Balancing",
        "topic": "Nginx Reverse Proxy & High-Availability Traffic Distribution",
        "hook": "সার্ভারে হঠাৎ ১০ গুণ ট্রাফিক আসলে সিঙ্গেল সার্ভার ক্র্যাশ না করে কীভাবে লোড ভাগ করবেন?",
        "summary": "এনজিনিক্স রিভার্স প্রক্সি এবং লিস্ট-কানেকশন অ্যালগরিদম ব্যবহার করে ট্রাফিক ডিস্ট্রিবিউশন ও জিরো-ডাউনটাইম নিশ্চিত করার আর্কিটেকচার।",
        "core_tech": ["Nginx", "Reverse Proxy", "Load Balancer", "Least Connections"],
        "scene_1_hook": "সার্ভারে হঠাৎ ১০ গুণ ট্রাফিক আসলে সিঙ্গেল সার্ভার ক্র্যাশ না করে কীভাবে লোড ভাগ করবেন? চলুন রিয়েল-লাইফ আর্কিটেকচার দেখে নেওয়া যাক।",
        "scene_2_problem": "সরাসরি অ্যাপ্লিকেশন সার্ভারে আনফিল্টার্ড রিকোয়েস্ট ঢুকলে মেমরি ও সিপিইউ ১০০% হয়ে নিমিষেই পুরো সিস্টেম ব্ল্যাকআউট হয়।",
        "scene_3_solution": "এনজিনিক্স রিভার্স প্রক্সিকে ফ্রন্ট গেটওয়ে বানিয়ে একাধিক ব্যাকএন্ড নোডে লোড ব্যালেন্স করলে কোনো নোড ডাউন হলেও ইউজার ট্রাফিক ড্রপ হয় না।",
        "scene_4_outro": "সফটওয়্যার ইঞ্জিনিয়ারিং ও সিস্টেম ডিজাইনের এমন প্রোডাকশন ওয়ার-স্টোরি জানতে এখনই সাবস্ক্রাইব করে পাশে থাকুন!"
    },
    {
        "category": "Database Engineering & Indexing",
        "topic": "PostgreSQL B-Tree vs Composite Indexing Optimization",
        "hook": "কোটি কোটি রো থাকা সত্ত্বেও কুয়েরি কেন মাত্র ৩ মিলিসেকেন্ডে ফিনিশ হয়?",
        "summary": "সাধারণ WHERE ক্লজে মাল্টিপল কলাম ফিল্টারের ক্ষেত্রে কম্পোজিট ইনডেক্সের লেফট-মোস্ট রুল ও কভারিং ইনডেক্সিং আর্কিটেকচার।",
        "core_tech": ["PostgreSQL", "B-Tree", "EXPLAIN ANALYZE", "Composite Index"],
        "scene_1_hook": "কোটি কোটি রো থাকা সত্ত্বেও প্রোডাকশন কুয়েরি কেন মাত্র ৩ মিলিসেকেন্ডে রেজাল্ট দেয়? এর পেছনের গোপন রহস্য জানুন।",
        "scene_2_problem": "ইনডেক্স ছাড়া ফুল টেবিল স্ক্যান চললে প্রতিটা সার্চে পুরো ডিস্ক রিড হয়, যা পিক-আওয়ারে ডেটাবেস কানেকশন পুল চোক করে দেয়।",
        "scene_3_solution": "কুয়েরি প্যাটার্ন অনুযায়ী কম্পোজিট বি-ট্রি ইনডেক্স সাজালে ডিস্ক আইও শূন্যের কোটায় নেমে আসে এবং ইন-মেমরি সিক দ্রুততম হয়।",
        "scene_4_outro": "ডেটাবেস পারফরম্যান্স ও ব্যাকএন্ড স্কেলিং সম্পর্কিত নিয়মিত আপডেটের জন্য এখনই ফলো ও শেয়ার করে রাখুন!"
    },
    {
        "category": "Distributed Caching & In-Memory Storage",
        "topic": "Redis Cache Aside vs Write-Through Strategy",
        "hook": "মিলিয়ন ট্রাফিকের চাপেও ডেটাবেসকে সুরক্ষিত রাখতে ক্যাশিং স্ট্র্যাটেজি কীভাবে কাজ করে?",
        "summary": "ক্যাশ অ্যাসাইড প্যাটার্ন, ক্যাশ স্ট্যাম্পিড প্রিভেনশন এবং ইনভ্যালিডেশন মেকানিজম ব্যবহার করে ৯৯% রিড অপটিমাইজেশন।",
        "core_tech": ["Redis", "Cache Aside", "TTL", "Distributed Locks"],
        "scene_1_hook": "মিলিয়ন ট্রাফিকের চাপেও মেইন ডেটাবেসকে সুরক্ষিত রেখে রেসপন্স টাইম ১০ মিলিসেকেন্ডের নিচে কীভাবে রাখবেন?",
        "scene_2_problem": "সরাসরি ডেটাবেসে বার বার একই রিড রিকোয়েস্ট গেলে সিপিইউ স্পাইক করে এবং ডেটাবেস ডেডলক পরিস্থিতিতে পড়ে।",
        "scene_3_solution": "রেডিস ইন-মেমোরি ক্যাশ লেয়ার বসিয়ে ক্যাশ-অ্যাসাইড ও স্মার্ট টিটিএল বসালে ৯৫% ডেটা সরাসরি মেমোরি থেকে সার্ভ করা সম্ভব।",
        "scene_4_outro": "সিস্টেম স্কেলিং ও রিয়েল-ওয়ার্ল্ড ক্লাউড টেকনোলজির আরও ইনসাইট পেতে এখনই সাবস্ক্রাইব ও কানেক্টেড থাকুন!"
    },
    {
        "category": "DevOps & Zero-Downtime Releases",
        "topic": "Docker Blue-Green Deployment & Connection Draining",
        "hook": "ব্যবহারকারীদের ৫xx এরর না দেখিয়ে কীভাবে রানিং প্রোডাকশন ভার্সন ইনস্ট্যান্ট আপগ্রেড করবেন?",
        "summary": "জিরো ডাউনটাইম ব্লু-গ্রিন ডেপ্লয়মেন্ট, অ্যাক্টিভ সকেট ড্রেনিং এবং ইনস্ট্যান্ট রোলব্যাক আর্কিটেকচার।",
        "core_tech": ["Docker", "Blue-Green", "CI/CD", "Reverse Proxy"],
        "scene_1_hook": "ব্যবহারকারীদের ৫xx এরর না দেখিয়ে কীভাবে লাইভ প্রোডাকশন ভার্সন সেকেন্ডের মধ্যে জিরো ডাউনটাইমে আপগ্রেড করবেন?",
        "scene_2_problem": "সার্ভারে সরাসরি কোড পুল করে প্রসেস রিস্টার্ট দিলে ট্রানজেকশনে থাকা শত শত ব্যবহারকারীর রিকোয়েস্ট ড্রপ হয়ে ইরর রিটার্ন করে।",
        "scene_3_solution": "ব্লু এবং গ্রিন দুটি প্যারালাল কন্টেইনার রেডি রেখে হেলথ-চেক পাসের পরই রিভার্স প্রক্সি দিয়ে ট্রাফিক রি-রুট করলেই জিরো ডাউনটাইম! ",
        "scene_4_outro": "প্রোডাকশন ডেভঅপ্স এবং কনটেইনার আর্কিটেকচারের নিয়মিত ভিডিওর জন্য এখনই সাবস্ক্রাইব করে রাখুন!"
    },
    {
        "category": "Event-Driven & Microservices",
        "topic": "Apache Kafka vs RabbitMQ: High-Throughput Event Streaming",
        "hook": "মাইক্রোসার্ভিসের মধ্যে প্রতি সেকেন্ডে ৫০ হাজার মেসেজ আদান-প্রদান করতে কোনটা সেরা?",
        "summary": "মেসেজ কিউ বনাম ডিস্ট্রিবিউটেড ইভেন্ট লগ, রিটেনশন পলিসি এবং ব্যাকপ্রেশার হ্যান্ডলিং কম্প্যারিজন।",
        "core_tech": ["Kafka", "RabbitMQ", "Event Driven", "Pub/Sub"],
        "scene_1_hook": "মাইক্রোসার্ভিসের মধ্যে প্রতি সেকেন্ডে ৫০ হাজার ইভেন্ট প্রসেস করতে ক্যাফকা নাকি র‍্যাবিট-এমকিউ—কোনটা আপনার প্রোডাকশনের জন্য সেরা?",
        "scene_2_problem": "সরাসরি সিঙ্ক্রোনাস এইচটিটিপি কল করলে একটি সার্ভিস ডাউন হলেই চেইন-রিঅ্যাকশনে পুরো ক্লাউড সিস্টেম ধসে পড়ে।",
        "scene_3_solution": "অ্যাসিনক্রোনাস ইভেন্ট বাস বসালে প্রডিউসার ও কনজিউমার সম্পূর্ণ ডিকাপল্ড থাকে এবং চরম ট্রাফিকেও ডেটা লস ছাড়াই কিউতে সিকিউর থাকে।",
        "scene_4_outro": "মাইক্রোসার্ভিস আর্কিটেকচার ও ক্লাউড সিস্টেমের অ্যাডভান্সড ইঞ্জিনিয়ারিং কনটেন্ট দেখতে সাবস্ক্রাইব করুন!"
    }
]

def plan_content(config, user_topic=None, user_hook=None):
    """
    Plans the content pillar and scene scripts using the chosen LLM or blueprint templates.
    """
    llm_cfg = config.get("llm", {})
    provider = llm_cfg.get("provider", "template").lower()

    if user_topic and user_hook:
        return {
            "category": "Software Architecture",
            "topic": user_topic,
            "hook": user_hook,
            "summary": f"প্রোডাকশন এনভায়রনমেন্টে {user_topic} সংক্রান্ত প্র্যাকটিক্যাল স্কেলিং আর্কিটেকচার।",
            "core_tech": [w.strip() for w in user_topic.split()[:4] if len(w.strip()) > 2],
            "scene_1_hook": f"{user_hook} চলুন বিস্তারিত দেখে নেওয়া যাক।",
            "scene_2_problem": f"{user_topic} সঠিকভাবে কনফিগার না করলে পিক ট্রাফিকে সিস্টেমের পারফরম্যান্স মারাত্মকভাবে ব্যাহত হয়।",
            "scene_3_solution": f"প্র্যাকটিক্যাল আর্কিটেকচার ও বেস্ট প্র্যাকটিস ফলো করলে ট্রাফিকের স্পাইক থাকা সত্ত্বেও সিস্টেম স্মুথলি স্কেল করে।",
            "scene_4_outro": "সফটওয়্যার ইঞ্জিনিয়ারিং ও সিস্টেম ডিজাইনের এমন প্রোডাকশন সমাধান পেতে এখনই সাবস্ক্রাইব করুন!"
        }

    # If external LLM is configured and not 'template'
    if provider in ["gemini", "openai", "openrouter", "custom"] and llm_cfg.get("api_key"):
        try:
            return call_external_llm(llm_cfg)
        except Exception as e:
            print(f"⚠️ LLM API failed ({e}), falling back gracefully to curated blueprint.")

    # Default / Template Blueprint
    blueprint = random.choice(CURATED_BLUEPRINTS)
    return dict(blueprint)

def call_external_llm(llm_cfg):
    provider = llm_cfg.get("provider")
    api_key = llm_cfg.get("api_key")
    model = llm_cfg.get("model", "gemini-2.5-flash")

    system_prompt = (
        "You are an elite Software Architecture and Tech Reel Director. "
        "Generate a high-retention 60-second developer video script in Bengali with a punchy psychological dilemma hook. "
        "Return STRICT valid JSON without markdown wrapping:\n"
        "{\n"
        '  "category": "Short Category (e.g. Database Engineering)",\n'
        '  "topic": "Concise Technical Title (e.g. Redis Cluster Replication)",\n'
        '  "hook": "Bengali psychological question hook (max 12 words)",\n'
        '  "summary": "1 sentence technical summary in Bengali",\n'
        '  "core_tech": ["Tech1", "Tech2", "Tech3"],\n'
        '  "scene_1_hook": "Bengali spoken script for 0-7s hook",\n'
        '  "scene_2_problem": "Bengali spoken script for 7-15s problem dilemma",\n'
        '  "scene_3_solution": "Bengali spoken script for 15-27s technical solution",\n'
        '  "scene_4_outro": "Bengali spoken script for 27-35s CTA and closing"\n'
        "}"
    )

    if provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": system_prompt}]}],
            "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)

    elif provider in ["openai", "openrouter", "custom"]:
        base_url = llm_cfg.get("base_url") or ("https://openrouter.ai/api/v1" if provider == "openrouter" else "https://api.openai.com/v1")
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a professional video script director. Always respond with raw valid JSON."},
                {"role": "user", "content": system_prompt}
            ],
            "temperature": 0.7
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_text = data["choices"][0]["message"]["content"]
            # Clean markdown if returned
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            return json.loads(raw_text.strip())

    raise ValueError(f"Unsupported provider: {provider}")
