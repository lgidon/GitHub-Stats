with metrics as (

    select * from {{ ref('int_pull_requests_metrics') }}

),

final as (

    select
        -- Primary Key
        pull_request_id,

        -- Natural Keys / Context
        pull_request_number,
        repo_owner,
        repo_name,
        author_username,
        author_type,

        -- Status Flags
        pr_state,
        is_draft,
        is_merged,
        is_closed_without_merge,

        -- Branch Context
        source_branch,
        target_branch,

        -- Timestamps
        created_at,
        updated_at,
        closed_at,
        merged_at,

        -- Pre-computed DORA Metrics
        round(time_to_merge_hours, 2) as time_to_merge_hours,
        round(total_open_hours, 2) as total_open_hours

    from metrics

)

select * from final