use std::{fs::File, io::Write, process::exit, sync::Arc};

use crate::{Config, ModelEndpoint};
use anyhow::{Context, Ok};
use axum::extract::State;
use comfy_table::{presets::UTF8_NO_BORDERS, Cell, ContentArrangement, Row, Table};
use hyper_rustls::HttpsConnector;
use hyper_util::{
  client::legacy::{connect::HttpConnector, Client},
  rt::TokioExecutor,
};
use indoc::formatdoc;
use strum::IntoEnumIterator;

pub type HyperClient = Client<HttpsConnector<HttpConnector>, axum::body::Body>;

pub type ServerState = State<Arc<Server>>;

#[derive(Clone, Debug)]
pub struct Server {
  pub config: Arc<Config>,
  pub hyper_client: HyperClient,
}

impl Server {
  pub fn new() -> anyhow::Result<Self> {
    let config = Config::from_env();
    let user_env_file = config.user_env_file();
    let local_config_path = "./llamakey_client.env";
    File::create(local_config_path)
      .with_context(|| format!("Failed to create {local_config_path}"))?
      .write_all(user_env_file.as_bytes())
      .with_context(|| format!("Failed to write envs to {local_config_path}"))?;

    let endpoints = config.available_endpoints();
    if endpoints.is_empty() {
      log::error!(
        "No API keys for supported APIs are detected in your environment variables. Please check."
      );
      exit(1);
    } else {
      let mut available_msg = "\n LlaMaKey server started. API endpoints availability below:\n".to_string();
      let mut table = Table::new();
      table
        .load_preset(UTF8_NO_BORDERS)
        .set_content_arrangement(ContentArrangement::Dynamic)
        .set_width(100)
        .set_header(vec![
          Cell::new("Name"),
          Cell::new("Base URL"),
          Cell::new("Credential"),
        ]);

      for endpoint in ModelEndpoint::iter() {
        if endpoints.contains(&endpoint) {
          table.add_row(Row::from([
            format!("✓ {endpoint}"),
            endpoint.base_url().to_string().replace("http://", "").replace("https://", ""),
            endpoint.masked_credentials(&config),
          ]));
        } else {
          table.add_row(Row::from([
            format!("✗ {endpoint}"),
            "-".to_string(),
            "-".to_string(),
          ]));
        }
      }
      available_msg.push_str(&table.to_string());
      log::info!("{available_msg}");
    }

    let message = formatdoc! { r#"

      On your client end, please run the following commands to set environment variables:

      {user_env_file}
      For your convenience, the commands above are dumped to `{local_config_path}`. You may copy it to your client and `source` it. For example:
      source {local_config_path} && python3 -c "import openai; openai.Completion.create(...)"

      Thank you for choosing LlaMaKey! 🦙🔑
      If you like it, please tell your friends and give us a star at http://llamakey.ai/. Otherwise, let us know how we can improve at hello@llamakey.ai
      "#
    };
    log::warn!("{message}");

    let rustls_client = hyper_rustls::HttpsConnectorBuilder::new()
      .with_native_roots()
      .context("Failed to build HTTP client with native roots")?
      .https_or_http()
      .enable_http1()
      .build();

    let hyper_client: HyperClient = Client::builder(TokioExecutor::new()).build(rustls_client);

    Ok(Server {
      config: Arc::new(config),
      hyper_client,
    })
  }
}
