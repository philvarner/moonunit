def generate_zappa_settings(*, template, region, username, stack_name,
                            source_bucket_name, assets_bucket_name):
    with open(template, 'r') as f:
        template_str = f.read()

    return template_str.format(region=region,
                               username=username,
                               stack_name=stack_name,
                               source_bucket_name=source_bucket_name,
                               assets_bucket_name=assets_bucket_name
                               )
