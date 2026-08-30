#!/usr/bin/env python3
"""
Unit test suite for Bonifade Technologies Marketing Swarm.
Tests department configs, alias mappings, keyword routing, and tool executions.
"""

import glob
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../agents")))
import orchestrator
import tools


class TestMarketingSwarm(unittest.TestCase):
    def setUp(self):
        self.orchestrator = orchestrator.SwarmOrchestrator()

    def test_department_configs_exist(self):
        expected_agents = [
            "marketer-head",
            "marketer-site-auditor",
            "marketer-seo",
            "marketer-copywriter",
            "marketer-creative",
            "marketer-media-buyer",
            "marketer-email",
            "marketer-social",
            "marketer-launch",
            "marketer-pricing",
            "marketer-competitor",
            "marketer-aso",
            "marketer-data",
            "marketer-editor",
        ]
        for agent_id in expected_agents:
            self.assertIn(agent_id, self.orchestrator.agents, f"Agent @{agent_id} not found in orchestrator")
            agent = self.orchestrator.agents[agent_id]
            self.assertTrue(len(agent.name) > 0, f"Agent {agent_id} has empty name")
            self.assertTrue(len(agent.role) > 0, f"Agent {agent_id} has empty role")
            self.assertTrue(len(agent.system_prompt) > 20, f"Agent {agent_id} has insufficient prompt")

    def test_agent_aliases_valid(self):
        for alias, mapped_id in orchestrator.AGENT_ALIASES.items():
            self.assertIn(
                mapped_id,
                self.orchestrator.agents,
                f"Alias '@{alias}' maps to unknown agent id '{mapped_id}'",
            )

    def test_keyword_routing(self):
        test_cases = [
            ("can you do a site audit on our landing page scored 0-100?", "marketer-site-auditor"),
            ("how should we format our llms.txt for GEO and search ranking?", "marketer-seo"),
            ("write a graded copy sales letter for our SaaS", "marketer-copywriter"),
            ("generate a maxfusion visual ad concept for our video campaign", "marketer-creative"),
            ("our Meta ad frequency is 4.5 and CPA doubled, make the kill call", "marketer-media-buyer"),
            ("write our 5-day welcome email sequence and schedule", "marketer-email"),
            ("write a contrarian post that will survive the feed algorithm", "marketer-social"),
            ("give me an hour by hour launch day schedule for product hunt", "marketer-launch"),
            ("what to charge and pricing tier using hormozi value equation?", "marketer-pricing"),
            ("what they run on meta ad library for our competitor", "marketer-competitor"),
            ("optimize our app store and play listing keywords with aso", "marketer-aso"),
            ("our a/b test has 1000 visitors vs 1200, check statistical significance", "marketer-data"),
            ("cuts the ai slop from this draft before anything ships", "marketer-editor"),
            ("as head of marketing mastermind, how do we structure our growth engine?", "marketer-head"),
        ]

        for query, expected_id in test_cases:
            target_agent = self.orchestrator.agents.get("ceo")
            lower_content = query.lower()

            for agent_id, agent in self.orchestrator.agents.items():
                if f"@{agent_id}" in lower_content or f"@{agent.name.lower()}" in lower_content:
                    target_agent = agent
                    break
            else:
                for alias, mapped_id in orchestrator.AGENT_ALIASES.items():
                    if f"@{alias}" in lower_content:
                        if mapped_id in self.orchestrator.agents:
                            target_agent = self.orchestrator.agents[mapped_id]
                            break
                else:
                    if any(k in lower_content for k in ["site audit", "audit score", "cro audit", "conversion friction", "scored 0-100", "site score"]):
                        target_agent = self.orchestrator.agents.get("marketer-site-auditor", target_agent)
                    elif any(k in lower_content for k in ["llms.txt", "geo", "seo lead", "search ranking", "perplexity", "google overview", "generative engine"]):
                        target_agent = self.orchestrator.agents.get("marketer-seo", target_agent)
                    elif any(k in lower_content for k in ["graded copy", "copywriter", "sales letter", "vsl script", "headline copy", "grade copy", "direct response copy"]):
                        target_agent = self.orchestrator.agents.get("marketer-copywriter", target_agent)
                    elif any(k in lower_content for k in ["creative strategist", "maxfusion", "ai ad", "visual ad", "ad storyboard", "ad creative", "video ad concept"]):
                        target_agent = self.orchestrator.agents.get("marketer-creative", target_agent)
                    elif any(k in lower_content for k in ["media buyer", "ad fatigue", "dead audience", "kill call", "roas", "cpa threshold", "ad spend", "kill calls"]):
                        target_agent = self.orchestrator.agents.get("marketer-media-buyer", target_agent)
                    elif any(k in lower_content for k in ["email sequence", "drip campaign", "email schedule", "welcome sequence", "soap opera sequence", "email marketer"]):
                        target_agent = self.orchestrator.agents.get("marketer-email", target_agent)
                    elif any(k in lower_content for k in ["survive the feed", "social manager", "linkedin post", "twitter thread", "x thread", "viral hook", "feed post"]):
                        target_agent = self.orchestrator.agents.get("marketer-social", target_agent)
                    elif any(k in lower_content for k in ["product hunt", "launch manager", "hour by hour", "launch day", "maker comment", "gtm launch"]):
                        target_agent = self.orchestrator.agents.get("marketer-launch", target_agent)
                    elif any(k in lower_content for k in ["pricing strategist", "pricing tier", "what to charge", "grand slam offer", "hormozi", "value equation", "pricing model", "tiers, offers"]):
                        target_agent = self.orchestrator.agents.get("marketer-pricing", target_agent)
                    elif any(k in lower_content for k in ["competitor analyst", "what they run on meta", "meta ad library", "competitor ad", "competitor teardown", "competitor angle"]):
                        target_agent = self.orchestrator.agents.get("marketer-competitor", target_agent)
                    elif any(k in lower_content for k in ["aso specialist", "app store", "play store", "play listing", "app store optimization", "app subtitle", "app keyword", "aso"]):
                        target_agent = self.orchestrator.agents.get("marketer-aso", target_agent)
                    elif any(k in lower_content for k in ["data analyst", "a/b test", "ab test", "statistical significance", "marketing dashboard", "cac", "ltv", "cohort analysis", "dashboards"]):
                        target_agent = self.orchestrator.agents.get("marketer-data", target_agent)
                    elif any(k in lower_content for k in ["ai slop", "cuts the ai slop", "anti-slop", "editorial review", "edit this", "cut the fluff", "slop check", "slop before anything ships"]):
                        target_agent = self.orchestrator.agents.get("marketer-editor", target_agent)
                    elif any(k in lower_content for k in ["head of marketing", "marketing mastermind", "cmo", "marketing mastermind"]):
                        target_agent = self.orchestrator.agents.get("marketer-head", target_agent)

            self.assertEqual(
                target_agent.agent_id,
                expected_id,
                f"Query '{query}' routed to @{target_agent.agent_id} instead of @{expected_id}",
            )

    def test_all_tools_execution(self):
        # 1. Site Audit
        res = tools.execute_tool("site_audit_score", {"url": "https://bonifadetechnologies.com"})
        self.assertTrue(res.get("ok"))
        self.assertIn("overall_score", res)

        # 2. llms.txt
        res = tools.execute_tool("generate_llms_txt", {"company_name": "Bonifade Technologies"})
        self.assertTrue(res.get("ok"))
        self.assertTrue(os.path.exists(res.get("path")))

        # 3. Grade copy
        res = tools.execute_tool("grade_copy", {"copy_text": "Stop wasting time. Our AI Swarm automates your business with 100% guarantee."})
        self.assertTrue(res.get("ok"))
        self.assertIn("grade", res)

        # 4. Anti-slop
        res = tools.execute_tool("anti_slop_check", {"text": "We delve into this transformative game-changer."})
        self.assertTrue(res.get("ok"))
        self.assertTrue(res.get("slop_index") > 0)

        # 5. Competitor Meta Ad Analyzer
        res = tools.execute_tool("competitor_meta_ad_analyzer", {"competitor_name": "Legacy Tech Corp"})
        self.assertTrue(res.get("ok"))
        self.assertIn("bonifade_counter_angles", res)

        # 6. Pricing Calculator
        res = tools.execute_tool("pricing_calculator", {"base_cost": 1000, "target_margin": 0.70})
        self.assertTrue(res.get("ok"))
        self.assertIn("pricing_tiers", res)

        # 7. A/B Test Calculator
        res = tools.execute_tool("ab_test_calculator", {"visitors_a": 1000, "conversions_a": 50, "visitors_b": 1000, "conversions_b": 85})
        self.assertTrue(res.get("ok"))
        self.assertTrue(res.get("statistically_significant"))

        # 8. Product Hunt Schedule
        res = tools.execute_tool("product_hunt_schedule", {"product_name": "Buzz Swarm OS", "tagline": "AI Swarm OS"})
        self.assertTrue(res.get("ok"))
        self.assertEqual(len(res.get("schedule")), 10)

        # 9. ASO Metadata Analyzer
        res = tools.execute_tool("aso_metadata_analyzer", {"app_name": "Buzz Swarm", "subtitle": "AI Automation", "keywords": "ai,agents,crm"})
        self.assertTrue(res.get("ok"))
        self.assertTrue(res.get("apple_app_store_compliant"))


if __name__ == "__main__":
    unittest.main()
