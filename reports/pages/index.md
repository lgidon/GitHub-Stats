# 🚀 GitHub DORA Metrics & Engineering Analytics

```sql pr_summary
SELECT 
    COUNT(*) as total_prs,
    COUNT(CASE WHEN is_merged THEN 1 END) as merged_prs,
    ROUND(AVG(time_to_merge_hours), 2) as avg_merge_hours
FROM github_stats.fct_pull_requests
```

```sql top_authors
SELECT 
    author_username,
    total_prs_submitted,
    total_prs_merged,
    avg_time_to_merge_hours
FROM github_stats.dim_authors
ORDER BY total_prs_merged DESC
LIMIT 10
```

<BigValue 
  data={pr_summary} 
  value=total_prs 
  title="Total PRs Analyzed" 
/>

<BigValue 
  data={pr_summary} 
  value=merged_prs 
  title="Merged PRs" 
/>

<BigValue 
  data={pr_summary} 
  value=avg_merge_hours 
  title="Avg Time to Merge" 
  unit=" hrs"
/>

---

## Top Contributors

<BarChart 
  data={top_authors} 
  x=author_username 
  y=total_prs_merged 
  title="Merged Pull Requests by Contributor"
  yAxisTitle="Merged PRs"
/>

<DataTable data={top_authors} search=true sort=avg_time_to_merge_hours>
  <Column id=author_username title="Contributor" />
  <Column id=total_prs_submitted title="PRs Submitted" />
  <Column id=total_prs_merged title="PRs Merged" />
  <Column id=avg_time_to_merge_hours title="Avg Merge Time (hrs)" />
</DataTable>