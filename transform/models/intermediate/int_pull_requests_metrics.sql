with staging as (

    select * from {{ ref('stg_github__pull_requests') }}

),

calculated as (

    select
        pull_request_id,
        pull_request_number,
        repo_owner,
        repo_name,
        author_username,
        author_type,
        pr_state,
        title,
        is_draft,
        source_branch,
        target_branch,
        
        -- Raw Timestamps
        created_at,
        updated_at,
        closed_at,
        merged_at,
        
        -- Boolean Flags
        (merged_at is not null) as is_merged,
        (closed_at is not null and merged_at is null) as is_closed_without_merge,
        
        -- DORA Metrics: Cycle Times
        -- 1. Time to Merge (from creation to merge)
        case 
            when merged_at is not null then date_diff('minute', created_at, merged_at) / 60.0
            else null 
        end as time_to_merge_hours,

        -- 2. PR Lifetime (from creation to close/merge or active age)
        case 
            when closed_at is not null then date_diff('minute', created_at, closed_at) / 60.0
            else date_diff('minute', created_at, current_timestamp) / 60.0
        end as total_open_hours

    from staging

)

select * from calculated