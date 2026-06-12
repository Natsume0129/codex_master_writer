# Original Plot Map

记录原作或主设定中的主要剧情节点，用于续写和剧情重构时判断保留、替换、反转或删除。

## Plot Nodes

```yaml
plot_nodes:
  - id: ""
    chapter: ""
    event: ""
    summary: ""
    causes: []
    effects: []
    required_conditions: []
    affected_characters: []
    affected_relationships: []
    affected_factions: []
    affected_items: []
    affected_world_rules: []
    foreshadowing_links: []
    can_survive_divergence: true
    replacement_needed_if_changed: false
    source: []
    confidence: "medium"
```

## Divergence Mapping Notes

- preserved_plot_nodes：分歧后仍可成立的原剧情节点。
- invalidated_plot_nodes：因前提变化失效的原剧情节点。
- inverted_plot_nodes：被反转功能的原剧情节点。
- replacement_plot_nodes：需要新设计替代的剧情节点。
