with source as (

    select * from {{ source('raw_github', 'stg_raw_pull_requests') }}

),

renamed as (

    select
        -- Identifiers
        id as pull_request_id,
        number as pull_request_number,
        node_id,
        
        -- Repository Context
        repo_owner,
        repo_name,
        
        -- State & Lifecycle
        state as pr_state,
        title,
        draft as is_draft,
        
        -- User Details (Extracting nested JSON keys)
        user.login as author_username,
        user.type as author_type,
        
        -- Timestamps (Casting ISO strings to TIMESTAMPTZ)
        created_at::timestamptz as created_at,
        updated_at::timestamptz as updated_at,
        closed_at::timestamptz as closed_at,
        merged_at::timestamptz as merged_at,
        
        -- Branch Meta
        head.ref as source_branch,
        base.ref as target_branch

    from source

)

select * from renamed