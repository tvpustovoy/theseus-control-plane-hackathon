// Read-only templates. Replace this synthetic organization id after connecting.
const org = "synthetic-demo";
db.claims.find({ organization_id: org, status: "candidate" },
  { subject: 1, predicate: 1, value: 1, source_id: 1, quote: 1 });
db.conflicts.find({ organization_id: org, status: "open" });
db.agent_specs.find({ organization_id: org, status: "proposed" },
  { intent: 1, allowed_tools: 1, data_scope: 1, budget: 1 });
db.culture_hypotheses.find({ organization_id: org, review_status: "unreviewed" });
db.events.aggregate([
  { $match: { organization_id: org } },
  { $group: { _id: { agent: "$agent_id", type: "$type" }, count: { $sum: 1 } } }
]);
