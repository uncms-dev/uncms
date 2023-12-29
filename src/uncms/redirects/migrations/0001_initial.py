from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Redirect",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("301", "Permanent"), ("302", "Temporary")],
                        default="301",
                        max_length=3,
                    ),
                ),
                (
                    "old_path",
                    models.CharField(
                        db_index=True,
                        help_text='This can either be a whole URL, or just a path excluding the domain name (starting with "/"); it will be normalised to a path when you save. Example: "https://www.example.com/events/" or "/events/".',
                        max_length=200,
                        unique=True,
                        verbose_name="redirect from",
                    ),
                ),
                (
                    "new_path",
                    models.CharField(
                        blank=True,
                        help_text="If you leave this empty, a 410 Gone response will be served for this URL.",
                        max_length=200,
                        verbose_name="redirect to",
                    ),
                ),
                (
                    "regular_expression",
                    models.BooleanField(
                        default=False,
                        help_text='This will allow using regular expressions to match and replace patterns in URLs. See the <a href="https://docs.python.org/3/library/re.html" rel="noopener noreferrer" target="_blank">Python regular expression documentation</a> for details.',
                    ),
                ),
                (
                    "test_path",
                    models.CharField(
                        blank=True,
                        help_text="You will need to specify a test path to ensure your regular expression is valid.",
                        max_length=200,
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "redirect",
                "verbose_name_plural": "redirects",
                "ordering": ("old_path",),
            },
        ),
    ]
